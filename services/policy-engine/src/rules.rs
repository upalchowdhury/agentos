use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum Rule {
    RateLimit {
        max_requests: u32,
        window_seconds: u64,
    },
    CostLimit {
        max_cost_cents: u64,
        window_seconds: u64,
    },
    RequireRole {
        roles: Vec<String>,
    },
    RequirePermission {
        resource: String,
        action: String,
    },
    AttributeMatch {
        attribute: String,
        operator: Operator,
        value: String,
    },
    BlockPII {
        types: Vec<PIIType>,
    },
    BlockToxicity {
        threshold: f32,
    },
    RequireContentCompliance {
        policies: Vec<String>,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum PIIType {
    SSN,
    CreditCard,
    Email,
    PhoneNumber,
    IPAddress,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Operator {
    Equals,
    NotEquals,
    Contains,
    GreaterThan,
    LessThan,
    In,
}

impl Rule {
    pub fn name(&self) -> &str {
        match self {
            Rule::RateLimit { .. } => "rate_limit",
            Rule::CostLimit { .. } => "cost_limit",
            Rule::RequireRole { .. } => "require_role",
            Rule::RequirePermission { .. } => "require_permission",
            Rule::AttributeMatch { .. } => "attribute_match",
            Rule::BlockPII { .. } => "block_pii",
            Rule::BlockToxicity { .. } => "block_toxicity",
            Rule::RequireContentCompliance { .. } => "require_content_compliance",
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rule_serialization() {
        let rule = Rule::RateLimit {
            max_requests: 100,
            window_seconds: 60,
        };

        let json = serde_json::to_string(&rule).unwrap();
        let deserialized: Rule = serde_json::from_str(&json).unwrap();

        match deserialized {
            Rule::RateLimit {
                max_requests,
                window_seconds,
            } => {
                assert_eq!(max_requests, 100);
                assert_eq!(window_seconds, 60);
            }
            _ => panic!("Wrong rule type"),
        }
    }
}
