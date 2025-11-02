# Model A Deployment Methods Comparison

## 📊 Quick Comparison

| Feature | UI Paste | Script Upload |
|---------|----------|---------------|
| **Speed** | ⚡ Fastest | 🔄 Moderate |
| **Complexity** | ✅ Simple | 🔧 Advanced |
| **Files** | Single | Multiple |
| **Dependencies** | ❌ None | ✅ requirements.txt |
| **Testing** | After deploy | Before deploy |
| **Telemetry** | Basic | Full ATP v0 |
| **Automation** | Manual | CI/CD ready |
| **Version Control** | Copy/paste | Git friendly |
| **Best For** | Prototypes | Production |

---

## Method 1: UI Paste Deployment

### When to Use
- ✅ Quick testing and prototyping
- ✅ Learning AgentOS
- ✅ Single-file agents
- ✅ No external dependencies needed
- ✅ Visual deployment preference

### Steps
1. Open `http://localhost:3001`
2. Click "Deploy Code (Model A)"
3. Paste from `agent_ui_simple.py`
4. Click deploy
5. Wait ~30 seconds
6. Test immediately

### Files Used
- `agent_ui_simple.py` - Simplified handler
- `UI_DEPLOYMENT_GUIDE.md` - Step-by-step guide
- `test_ui_deployed.sh` - Quick testing script

### Code Structure
```python
def handler(event):
    input_data = event.get("input_data", {})
    # Your logic here
    return {
        "result": {...},
        "cost": 0.0001
    }
```

**Pros:**
- ⚡ Fastest deployment (2 minutes)
- 👀 Visual feedback
- 📝 No command line needed
- 🎯 Perfect for demos

**Cons:**
- 📦 No external dependencies
- 📊 Limited telemetry
- 🔄 Manual re-deployment
- 📝 No local testing

---

## Method 2: Script Deployment (API)

### When to Use
- ✅ Production deployments
- ✅ Need external packages (numpy, requests, etc.)
- ✅ Want ATP v0 telemetry
- ✅ CI/CD pipelines
- ✅ Multiple files needed
- ✅ Version control with git

### Steps
1. Edit code locally
2. Test with `python test_local.py`
3. Run `./register_agent.sh`
4. Script handles everything
5. Test with `./invoke_agent.sh <id>`

### Files Used
- `agent.py` - Full handler with telemetry
- `requirements.txt` - Dependencies
- `register_agent.sh` - Automated deployment
- `invoke_agent.sh` - Testing script
- `test_local.py` - Local tests

### Code Structure
```python
def handler(event):
    """Full handler with context"""
    start_time = time.time()
    
    input_data = event.get("input_data", {})
    context = event.get("context", {})
    
    # Your logic
    
    # ATP v0 telemetry
    telemetry = {
        "trace": {
            "trace_id": context.get("invocation_id"),
            "steps": [...]
        }
    }
    
    return {
        "result": {...},
        "telemetry": telemetry,
        "cost": 0.0001
    }
```

**Pros:**
- 📦 Full dependency support
- 📊 Complete ATP v0 traces
- 🧪 Test before deploy
- 🤖 CI/CD ready
- 📁 Multiple files
- 🔄 Easy updates

**Cons:**
- ⏱️ Slightly slower setup
- 🖥️ Requires command line
- 📚 More files to manage

---

## Which Method Should I Use?

### Use UI Paste if you're:
- 🎓 Learning AgentOS
- 🚀 Doing a quick demo
- 🧪 Testing a concept
- ✍️ Writing simple logic
- 👀 Want visual feedback

### Use Script Method if you need:
- 📦 External packages (numpy, pandas, requests)
- 📊 Full observability/traces
- 🧪 Local testing first
- 🤖 Automated deployments
- 📁 Multiple code files
- 🏭 Production readiness

---

## Example: Same Agent, Both Methods

### UI Paste Version (`agent_ui_simple.py`)
```python
def handler(event):
    numbers = event.get("input_data", {}).get("numbers", [])
    return {
        "result": {"sum": sum(numbers)},
        "cost": 0.0001
    }
```
**Lines of code: 5**

### Script Version (`agent.py`)
```python
def handler(event):
    start_time = time.time()
    input_data = event.get("input_data", {})
    context = event.get("context", {})
    
    numbers = input_data.get("numbers", [])
    result = sum(numbers)
    
    # ATP v0 telemetry
    telemetry = {
        "trace": {
            "trace_id": context.get("invocation_id"),
            "status": "SUCCESS",
            "execution_time_ms": int((time.time() - start_time) * 1000),
            "steps": [...]
        }
    }
    
    return {
        "result": {"sum": result},
        "telemetry": telemetry,
        "cost": 0.0001
    }
```
**Lines of code: 25+ (with full telemetry)**

---

## Migration Path

### Start with UI → Move to Script

1. **Prototype in UI**
   - Paste simple version
   - Test functionality
   - Validate approach

2. **Enhance Locally**
   - Copy to `agent.py`
   - Add telemetry
   - Add dependencies
   - Write tests

3. **Deploy via Script**
   - Run `./register_agent.sh`
   - Automate testing
   - Setup CI/CD

---

## Testing Commands

### After UI Deployment
```bash
# Quick test
./test_ui_deployed.sh <agent-id>
```

### After Script Deployment
```bash
# Full test suite
./invoke_agent.sh <agent-id>

# Or individual tests
python test_local.py
```

---

## Summary

**Both methods are valid!**

- 🎯 UI Paste: Fast prototyping and demos
- 🏭 Script Upload: Production and complex agents

**Start simple, grow as needed.**

Begin with UI paste for your first agent, then migrate to scripts when you need more power!
