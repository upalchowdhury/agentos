import { Pool } from 'pg';

export interface Role {
  name: string;
  description?: string;
}

export interface Permission {
  resource: string;
  action: string;
  constraints?: Record<string, any>;
}

export interface RoleWithPermissions extends Role {
  permissions: Permission[];
}

export class RBACManager {
  constructor(private pool: Pool) {}

  async assignRole(agentDID: string, roleName: string, grantedBy?: string): Promise<void> {
    if (!agentDID || !roleName) {
      throw new Error('agentDID and roleName are required');
    }

    const query = `
      INSERT INTO agent_roles (agent_did, role_name, granted_by) 
      VALUES ($1, $2, $3)
      ON CONFLICT (agent_did, role_name) DO NOTHING
    `;
    await this.pool.query(query, [agentDID, roleName, grantedBy || 'system']);
  }

  async revokeRole(agentDID: string, roleName: string): Promise<void> {
    if (!agentDID || !roleName) {
      throw new Error('agentDID and roleName are required');
    }

    const query = 'DELETE FROM agent_roles WHERE agent_did = $1 AND role_name = $2';
    await this.pool.query(query, [agentDID, roleName]);
  }

  async getAgentRoles(agentDID: string): Promise<string[]> {
    if (!agentDID) {
      throw new Error('agentDID is required');
    }

    const query = `
      SELECT role_name 
      FROM agent_roles 
      WHERE agent_did = $1 
        AND (expires_at IS NULL OR expires_at > NOW())
    `;
    const result = await this.pool.query(query, [agentDID]);
    return result.rows.map(row => row.role_name);
  }

  async getRolePermissions(roleName: string): Promise<Permission[]> {
    if (!roleName) {
      throw new Error('roleName is required');
    }

    const query = `
      SELECT resource, action, constraints 
      FROM permissions 
      WHERE role_name = $1
    `;
    const result = await this.pool.query(query, [roleName]);
    return result.rows.map(row => ({
      resource: row.resource,
      action: row.action,
      constraints: row.constraints || undefined,
    }));
  }

  async checkPermission(
    agentDID: string,
    resource: string,
    action: string,
    context?: Record<string, any>
  ): Promise<boolean> {
    if (!agentDID || !resource || !action) {
      throw new Error('agentDID, resource, and action are required');
    }

    const roles = await this.getAgentRoles(agentDID);

    for (const role of roles) {
      const permissions = await this.getRolePermissions(role);

      for (const perm of permissions) {
        if (this.matchesPermission(perm, resource, action, context || {})) {
          return true;
        }
      }
    }

    return false;
  }

  async listAllRoles(): Promise<Role[]> {
    const query = 'SELECT name, description FROM roles ORDER BY name';
    const result = await this.pool.query(query);
    return result.rows.map(row => ({
      name: row.name,
      description: row.description,
    }));
  }

  async createRole(name: string, description?: string): Promise<void> {
    if (!name) {
      throw new Error('role name is required');
    }

    const query = `
      INSERT INTO roles (name, description) 
      VALUES ($1, $2)
      ON CONFLICT (name) DO UPDATE SET description = $2
    `;
    await this.pool.query(query, [name, description || null]);
  }

  async addPermission(
    roleName: string,
    resource: string,
    action: string,
    constraints?: Record<string, any>
  ): Promise<void> {
    if (!roleName || !resource || !action) {
      throw new Error('roleName, resource, and action are required');
    }

    const query = `
      INSERT INTO permissions (role_name, resource, action, constraints)
      VALUES ($1, $2, $3, $4)
    `;
    await this.pool.query(query, [roleName, resource, action, constraints || null]);
  }

  private matchesPermission(
    perm: Permission,
    resource: string,
    action: string,
    context: Record<string, any>
  ): boolean {
    // Wildcard permissions
    if (perm.resource === '*' && perm.action === '*') {
      return true;
    }

    // Resource wildcard
    if (perm.resource === '*' && perm.action === action) {
      return true;
    }

    // Action wildcard
    if (perm.resource === resource && perm.action === '*') {
      return true;
    }

    // Exact match
    if (perm.resource !== resource || perm.action !== action) {
      return false;
    }

    // ABAC: Check constraints
    if (perm.constraints) {
      return this.evaluateConstraints(perm.constraints, context);
    }

    return true;
  }

  private evaluateConstraints(
    constraints: Record<string, any>,
    context: Record<string, any>
  ): boolean {
    for (const [key, expected] of Object.entries(constraints)) {
      const actual = context[key];

      if (Array.isArray(expected)) {
        if (!expected.includes(actual)) {
          return false;
        }
      } else if (typeof expected === 'object' && expected !== null) {
        const operator = expected.operator;
        const value = expected.value;

        if (!this.evaluateOperator(operator, actual, value)) {
          return false;
        }
      } else {
        if (actual !== expected) {
          return false;
        }
      }
    }
    return true;
  }

  private evaluateOperator(operator: string, actual: any, expected: any): boolean {
    switch (operator) {
      case 'equals':
        return actual === expected;
      case 'not_equals':
        return actual !== expected;
      case 'contains':
        return String(actual).includes(String(expected));
      case 'greater_than':
        return Number(actual) > Number(expected);
      case 'less_than':
        return Number(actual) < Number(expected);
      case 'in':
        return Array.isArray(expected) && expected.includes(actual);
      default:
        return false;
    }
  }
}
