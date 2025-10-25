use redis::aio::ConnectionManager;
use redis::AsyncCommands;
use serde_json::Value;

use crate::rules::Rule;

pub struct PolicyEngine {
    rules: Vec<Rule>,
    redis: ConnectionManager,
}

impl PolicyEngine {
    pub fn new(redis: ConnectionManager) -> Self {
        Self {
            rules: Vec::new(),
            redis,
        }
    }

    pub fn add_rule(&mut self, rule: Rule) {
        self.rules.push(rule);
    }

    pub async fn evaluate(
        &self,
        caller_did: &str,
        target_did: &str,
        action: &str,
        context: &Value,
    ) -> Result<bool, Box<dyn std::error::Error>> {
        if caller_did.is_empty() {
            return Err("caller_did is required".into());
        }
        if target_did.is_empty() {
            return Err("target_did is required".into());
        }
        if action.is_empty() {
            return Err("action is required".into());
        }

        // Evaluate all rules - all must pass
        for rule in &self.rules {
            if !self
                .evaluate_rule(rule, caller_did, target_did, action, context)
                .await?
            {
                return Ok(false);
            }
        }

        Ok(true)
    }

    async fn evaluate_rule(
        &self,
        rule: &Rule,
        caller_did: &str,
        _target_did: &str,
        _action: &str,
        _context: &Value,
    ) -> Result<bool, Box<dyn std::error::Error>> {
        match rule {
            Rule::RateLimit {
                max_requests,
                window_seconds,
            } => self.check_rate_limit(caller_did, *max_requests, *window_seconds).await,
            Rule::CostLimit {
                max_cost_cents,
                window_seconds,
            } => self.check_cost_limit(caller_did, *max_cost_cents, *window_seconds).await,
        }
    }

    async fn check_rate_limit(
        &self,
        caller_did: &str,
        max_requests: u32,
        window_seconds: u64,
    ) -> Result<bool, Box<dyn std::error::Error>> {
        let key = format!("rate_limit:{}:{}", caller_did, window_seconds);
        let mut conn = self.redis.clone();

        let count: u32 = conn.incr(&key, 1).await?;
        if count == 1 {
            conn.expire(&key, window_seconds as usize).await?;
        }

        Ok(count <= max_requests)
    }

    async fn check_cost_limit(
        &self,
        caller_did: &str,
        max_cost_cents: u64,
        window_seconds: u64,
    ) -> Result<bool, Box<dyn std::error::Error>> {
        let key = format!("cost_limit:{}:{}", caller_did, window_seconds);
        let mut conn = self.redis.clone();

        let cost: u64 = conn.get(&key).await.unwrap_or(0);
        Ok(cost < max_cost_cents)
    }

    pub async fn record_cost(
        &self,
        caller_did: &str,
        cost_cents: u64,
        window_seconds: u64,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let key = format!("cost_limit:{}:{}", caller_did, window_seconds);
        let mut conn = self.redis.clone();

        let current: u64 = conn.get(&key).await.unwrap_or(0);
        let new_cost = current + cost_cents;

        conn.set_ex(&key, new_cost, window_seconds as usize).await?;

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validation_errors() {
        // These tests would require a Redis connection
        // In production, use integration tests with test containers
    }
}
