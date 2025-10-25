use actix_web::{web, App, HttpResponse, HttpServer};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::RwLock;
use redis::aio::ConnectionManager;

mod engine;
mod rules;

use engine::PolicyEngine;
use rules::Rule;

#[derive(Debug, Deserialize)]
struct PolicyRequest {
    caller_did: String,
    target_did: String,
    action: String,
    context: serde_json::Value,
}

#[derive(Debug, Serialize)]
struct PolicyResponse {
    allowed: bool,
    reason: Option<String>,
}

#[derive(Debug, Deserialize)]
struct CostRequest {
    caller_did: String,
    cost_cents: u64,
    window_seconds: u64,
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    env_logger::init();

    // Initialize Redis cache
    let redis_url = std::env::var("REDIS_URL").unwrap_or_else(|_| "redis://localhost:6379".to_string());
    let redis_client = redis::Client::open(redis_url).expect("Failed to connect to Redis");
    let redis_conn = ConnectionManager::new(redis_client)
        .await
        .expect("Failed to create Redis connection manager");

    // Initialize policy engine
    let engine = Arc::new(RwLock::new(PolicyEngine::new(redis_conn)));

    // Load default rules
    load_default_rules(&engine).await;

    let engine_data = web::Data::new(engine);

    log::info!("Starting policy engine on 0.0.0.0:8081");

    HttpServer::new(move || {
        App::new()
            .app_data(engine_data.clone())
            .route("/api/v1/evaluate", web::post().to(evaluate))
            .route("/api/v1/rules", web::post().to(add_rule))
            .route("/api/v1/cost", web::post().to(record_cost))
            .route("/health", web::get().to(health))
    })
    .bind(("0.0.0.0", 8081))?
    .run()
    .await
}

async fn evaluate(
    req: web::Json<PolicyRequest>,
    engine: web::Data<Arc<RwLock<PolicyEngine>>>,
) -> HttpResponse {
    let engine = engine.read().await;

    match engine
        .evaluate(&req.caller_did, &req.target_did, &req.action, &req.context)
        .await
    {
        Ok(allowed) => HttpResponse::Ok().json(PolicyResponse {
            allowed,
            reason: if allowed {
                None
            } else {
                Some("Policy denied".into())
            },
        }),
        Err(e) => HttpResponse::InternalServerError().json(PolicyResponse {
            allowed: false,
            reason: Some(format!("Evaluation error: {}", e)),
        }),
    }
}

async fn add_rule(
    rule: web::Json<Rule>,
    engine: web::Data<Arc<RwLock<PolicyEngine>>>,
) -> HttpResponse {
    let mut engine = engine.write().await;
    engine.add_rule(rule.into_inner());
    HttpResponse::Ok().json(serde_json::json!({"status": "rule added"}))
}

async fn record_cost(
    req: web::Json<CostRequest>,
    engine: web::Data<Arc<RwLock<PolicyEngine>>>,
) -> HttpResponse {
    let engine = engine.read().await;

    match engine
        .record_cost(&req.caller_did, req.cost_cents, req.window_seconds)
        .await
    {
        Ok(_) => HttpResponse::Ok().json(serde_json::json!({"status": "cost recorded"})),
        Err(e) => HttpResponse::InternalServerError().json(serde_json::json!({
            "error": format!("Failed to record cost: {}", e)
        })),
    }
}

async fn health() -> HttpResponse {
    HttpResponse::Ok().json(serde_json::json!({"status": "healthy"}))
}

async fn load_default_rules(engine: &Arc<RwLock<PolicyEngine>>) {
    let mut engine = engine.write().await;

    // Rate limit rule: max 100 requests per minute per agent
    engine.add_rule(Rule::RateLimit {
        max_requests: 100,
        window_seconds: 60,
    });

    // Cost limit rule: max $10 per hour per agent
    engine.add_rule(Rule::CostLimit {
        max_cost_cents: 1000,
        window_seconds: 3600,
    });

    log::info!("Loaded default policy rules");
}
