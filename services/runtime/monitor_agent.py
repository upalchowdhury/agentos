#!/usr/bin/env python3
"""
AgentOS Real-time Monitoring Dashboard
Monitors agent deployments, invocations, RBAC, and security events
"""

import psycopg2
import sys
from datetime import datetime, timedelta
from typing import Optional


class AgentMonitor:
    def __init__(self, host="localhost", port=5432, dbname="agentos", user="postgres", password="postgres"):
        try:
            self.conn = psycopg2.connect(
                host=host,
                port=port,
                dbname=dbname,
                user=user,
                password=password
            )
            self.cur = self.conn.cursor()
        except psycopg2.OperationalError as e:
            print(f"❌ Database connection failed: {e}")
            print("\nMake sure PostgreSQL is running:")
            print("  docker ps | grep agentos-postgres")
            sys.exit(1)
    
    def print_header(self, title: str):
        print("\n" + "=" * 100)
        print(f"{title}")
        print("=" * 100)
    
    def print_section(self, title: str):
        print(f"\n{title}")
        print("-" * 100)
    
    def get_active_agents(self):
        """Display all active (RUNNING) agents"""
        self.print_section("📊 ACTIVE AGENTS")
        
        self.cur.execute("""
            SELECT 
                agent_did,
                status,
                deployed_at,
                resource_limits->>'max_memory' as memory,
                resource_limits->>'max_cpu' as cpu
            FROM agent_deployments
            WHERE status = 'RUNNING'
            ORDER BY deployed_at DESC
        """)
        
        results = self.cur.fetchall()
        
        if results:
            for row in results:
                print(f"   • Agent: {row[0]}")
                print(f"     Status: {row[1]} | Deployed: {row[2]} | Memory: {row[3]} | CPU: {row[4]}")
        else:
            print("   No active agents")
    
    def get_recent_invocations(self, hours: int = 1):
        """Display invocation statistics for last N hours"""
        self.print_section(f"📈 INVOCATIONS (Last {hours} Hour{'s' if hours > 1 else ''})")
        
        time_threshold = datetime.now() - timedelta(hours=hours)
        
        self.cur.execute("""
            SELECT 
                agent_did,
                COUNT(*) as total_invocations,
                COUNT(*) FILTER (WHERE status = 'SUCCESS') as successful,
                COUNT(*) FILTER (WHERE status = 'ERROR') as errors,
                COUNT(*) FILTER (WHERE status = 'TIMEOUT') as timeouts,
                ROUND(AVG(execution_time_ms)::numeric, 2) as avg_time_ms,
                SUM(cost_cents) as total_cost
            FROM agent_invocations
            WHERE invoked_at > %s
            GROUP BY agent_did
            ORDER BY total_invocations DESC
        """, (time_threshold,))
        
        results = self.cur.fetchall()
        
        if results:
            for row in results:
                success_rate = (row[2] / row[1] * 100) if row[1] > 0 else 0
                print(f"   • Agent: {row[0]}")
                print(f"     Invocations: {row[1]} | Success: {row[2]} ({success_rate:.1f}%) | Errors: {row[3]} | Timeouts: {row[4]}")
                print(f"     Avg Time: {row[5]}ms | Total Cost: ${row[6]/100:.4f}")
        else:
            print(f"   No invocations in the last {hours} hour(s)")
    
    def get_error_analysis(self, hours: int = 1):
        """Display detailed error analysis"""
        self.print_section("⚠️  ERROR ANALYSIS")
        
        time_threshold = datetime.now() - timedelta(hours=hours)
        
        self.cur.execute("""
            SELECT 
                agent_did,
                status,
                COUNT(*) as count,
                ARRAY_AGG(DISTINCT error_message) FILTER (WHERE error_message IS NOT NULL) as error_messages
            FROM agent_invocations
            WHERE invoked_at > %s AND status != 'SUCCESS'
            GROUP BY agent_did, status
            ORDER BY count DESC
        """, (time_threshold,))
        
        results = self.cur.fetchall()
        
        if results:
            for row in results:
                print(f"   • Agent: {row[0]} | Status: {row[1]} | Count: {row[2]}")
                if row[3]:
                    for error_msg in row[3]:
                        if error_msg:
                            print(f"     Error: {error_msg}")
        else:
            print(f"   ✅ No errors in the last {hours} hour(s)")
    
    def get_performance_metrics(self):
        """Display performance percentiles"""
        self.print_section("⚡ PERFORMANCE METRICS")
        
        self.cur.execute("""
            SELECT 
                agent_did,
                COUNT(*) as total,
                ROUND(AVG(execution_time_ms)::numeric, 2) as avg_ms,
                ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY execution_time_ms)::numeric, 2) as p50_ms,
                ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY execution_time_ms)::numeric, 2) as p95_ms,
                ROUND(PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY execution_time_ms)::numeric, 2) as p99_ms,
                MIN(execution_time_ms) as min_ms,
                MAX(execution_time_ms) as max_ms
            FROM agent_invocations
            WHERE invoked_at > NOW() - INTERVAL '1 hour'
            GROUP BY agent_did
        """)
        
        results = self.cur.fetchall()
        
        if results:
            for row in results:
                print(f"   • Agent: {row[0]}")
                print(f"     Samples: {row[1]} | Avg: {row[2]}ms | P50: {row[3]}ms | P95: {row[4]}ms | P99: {row[5]}ms")
                print(f"     Min: {row[6]}ms | Max: {row[7]}ms")
        else:
            print("   No performance data available")
    
    def get_security_audit(self, hours: int = 1):
        """Display RBAC audit logs"""
        self.print_section(f"🔒 SECURITY AUDIT (Last {hours} Hour{'s' if hours > 1 else ''})")
        
        time_threshold = datetime.now() - timedelta(hours=hours)
        
        try:
            # Check if audit table exists
            self.cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'agent_audit_logs'
                );
            """)
            
            if not self.cur.fetchone()[0]:
                print("   ℹ️  RBAC audit table not yet created")
                print("   Run: docker exec -i agentos-postgres psql -U postgres -d agentos < infra/migrations/003_rbac_schema.sql")
                return
            
            self.cur.execute("""
                SELECT 
                    action,
                    status,
                    COUNT(*) as count
                FROM agent_audit_logs
                WHERE timestamp > %s
                GROUP BY action, status
                ORDER BY count DESC
            """, (time_threshold,))
            
            results = self.cur.fetchall()
            
            if results:
                for row in results:
                    status_icon = "✅" if row[1] == "allowed" else "🚫"
                    print(f"   {status_icon} {row[0]}: {row[2]} attempts ({row[1]})")
            else:
                print(f"   No security events in the last {hours} hour(s)")
                
            # Check for denied access
            self.cur.execute("""
                SELECT 
                    agent_did,
                    action,
                    resource,
                    timestamp
                FROM agent_audit_logs
                WHERE timestamp > %s AND status = 'denied'
                ORDER BY timestamp DESC
                LIMIT 10
            """, (time_threshold,))
            
            denied = self.cur.fetchall()
            if denied:
                print("\n   🚫 DENIED ACCESS ATTEMPTS:")
                for row in denied:
                    print(f"      Agent: {row[0]} | Action: {row[1]} | Resource: {row[2]} | Time: {row[3]}")
                    
        except psycopg2.errors.UndefinedTable:
            print("   ℹ️  RBAC audit table not yet created")
        except Exception as e:
            print(f"   ⚠️  Error retrieving audit logs: {e}")
    
    def get_cost_analysis(self):
        """Display cost analysis"""
        self.print_section("💰 COST ANALYSIS")
        
        self.cur.execute("""
            SELECT 
                agent_did,
                COUNT(*) as invocations,
                SUM(cost_cents) as total_cost_cents,
                AVG(cost_cents) as avg_cost_cents
            FROM agent_invocations
            WHERE invoked_at > NOW() - INTERVAL '24 hours'
            GROUP BY agent_did
            ORDER BY total_cost_cents DESC
        """)
        
        results = self.cur.fetchall()
        
        if results:
            total_cost = sum(row[2] for row in results)
            print(f"   Total Cost (24h): ${total_cost/100:.4f}\n")
            
            for row in results:
                print(f"   • Agent: {row[0]}")
                print(f"     Invocations: {row[1]} | Total: ${row[2]/100:.4f} | Avg: ${row[3]/100:.4f}")
        else:
            print("   No cost data available")
    
    def get_agent_stats_view(self):
        """Query the agent_stats view"""
        self.print_section("📊 AGENT STATISTICS (Aggregated View)")
        
        self.cur.execute("""
            SELECT 
                agent_did,
                status,
                total_invocations,
                total_cost_cents,
                avg_execution_time_ms,
                last_invoked_at
            FROM agent_stats
            ORDER BY total_invocations DESC
            LIMIT 10
        """)
        
        results = self.cur.fetchall()
        
        if results:
            for row in results:
                print(f"   • Agent: {row[0]} | Status: {row[1]}")
                print(f"     Total Invocations: {row[2]} | Total Cost: ${row[3]/100:.4f}")
                print(f"     Avg Time: {row[4]:.2f}ms | Last Invoked: {row[5]}")
        else:
            print("   No statistics available")
    
    def run_full_dashboard(self):
        """Run complete monitoring dashboard"""
        self.print_header(f"AGENTOS MONITORING DASHBOARD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            self.get_active_agents()
            self.get_recent_invocations(hours=1)
            self.get_error_analysis(hours=1)
            self.get_performance_metrics()
            self.get_cost_analysis()
            self.get_security_audit(hours=1)
            self.get_agent_stats_view()
            
            print("\n" + "=" * 100)
            print("✅ Monitoring dashboard complete")
            print("=" * 100 + "\n")
            
        except Exception as e:
            print(f"\n❌ Error running dashboard: {e}")
            import traceback
            traceback.print_exc()
    
    def close(self):
        """Close database connection"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()


def main():
    monitor = AgentMonitor()
    
    try:
        monitor.run_full_dashboard()
    finally:
        monitor.close()


if __name__ == "__main__":
    main()
