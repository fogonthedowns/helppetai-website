# Production Debugging Retrospective: SSL + Pydantic Issues

**Date:** September 2, 2025  
**Duration:** ~3 hours  
**Impact:** Complete production outage  
**Root Causes:** Multiple compounding issues  

## Summary

A production deployment failure cascaded into multiple interconnected issues involving SSL configuration, Pydantic validation, and resource constraints. What started as audio recording issues evolved into a complete production outage requiring systematic debugging.

## Timeline of Events

### Initial Problem Report
- **Issue:** Audio recording upload success but no playback capability
- **User Request:** Fix audio playback and visit transcript visibility
- **Scope:** Appeared to be frontend/audio handling issue

### Problem Evolution
1. **Audio Format Issues** - WebM vs MP3 requirements
2. **Database Connection Failures** - SSL configuration problems  
3. **Container Resource Exhaustion** - Low CPU/memory limits
4. **Pydantic Validation Errors** - Schema mismatches with database
5. **Complete Production Outage** - No API endpoints responding

## Root Cause Analysis

### 1. SSL Configuration Mismatch
**Problem:** RDS PostgreSQL required SSL encryption, but application was configured with `RDS_SSL_MODE=disable`

**Error:** `no pg_hba.conf entry for host "172.31.22.245", user "helppetadmin", database "postgres", no encryption`

**Contributing Factors:**
- AsyncPG driver uses `ssl=` parameter, not `sslmode=` (like psycopg2)
- Initial fix attempted wrong parameter name
- Environment variable misconfiguration in ECS task definition

**Resolution:**
```python
# Fixed in config.py
rds_ssl_mode: str = Field(default="require", env="RDS_SSL_MODE")

# AsyncPG URL (correct)
f"postgresql+asyncpg://...?ssl={self.rds_ssl_mode}"

# Psycopg2 URL (correct) 
f"postgresql+psycopg2://...?sslmode={self.rds_ssl_mode}"
```

### 2. Resource Constraints
**Problem:** ECS container running with insufficient resources

**Configuration:**
```makefile
# Before (insufficient)
TASK_CPU = 256      # 0.25 vCPU
TASK_MEMORY = 512   # 512 MB

# After (adequate)  
TASK_CPU = 512      # 0.5 vCPU
TASK_MEMORY = 1024  # 1 GB
```

**Impact:** Random 500 errors due to memory/CPU exhaustion during database operations

### 3. Pydantic Schema Mismatch
**Problem:** Pydantic models didn't match database schema

**Database Schema:**
```python
email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
```

**Pydantic Schema (Incorrect):**
```python
# Before - Required field
email: str

# After - Optional field  
email: Optional[str] = None
```

**Error:** `1 validation error for UserResponse` when trying to serialize users with NULL email values

### 4. Poor Error Reporting
**Problem:** Generic error messages provided no actionable information

**Before:**
```
ERROR - Global exception: 1 validation error for UserResponse
```

**After:**
```python
# Detailed validation error handler
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc: ValidationError):
    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"], 
            "type": error["type"],
            "input": error.get("input")
        })
```

## What Went Wrong

### 1. **Cascading Failures**
- Single SSL misconfiguration caused multiple downstream failures
- Each attempted fix introduced new issues
- Lack of systematic approach led to trial-and-error debugging

### 2. **Insufficient Monitoring**
- No clear visibility into container resource usage
- Generic error messages masked root causes
- Missing database connection health checks

### 3. **Environment Inconsistency**
- Local development worked while production failed
- SSL requirements differed between environments
- Schema validation differences not caught in testing

### 4. **Debugging Inefficiency**
- Spent significant time on symptoms rather than root causes
- Multiple deployment cycles for single logical fixes
- Lack of systematic validation of assumptions

## Lessons Learned

### 1. **System Design**
- **Database connections should fail fast with clear errors**
- **Environment parity is critical** - SSL/resource configs should match
- **Resource limits should have safety margins** for production workloads

### 2. **Error Handling**
- **Generic error messages are debugging poison**
- **Validation errors must show field-level details**
- **Include request context in all error logs**

### 3. **Development Process**
- **Schema changes need migration AND validation updates**
- **Environment-specific configs should be documented**
- **Resource requirements should be load-tested**

### 4. **Debugging Strategy**
- **Start with infrastructure (DB, network, resources)**
- **Verify assumptions with direct testing (curl, psql)**
- **Fix root causes, not symptoms**

## Action Items for Future

### Immediate (Next Sprint)
- [ ] **Add comprehensive health checks** including database connectivity
- [ ] **Document all environment variables** and their production values  
- [ ] **Add resource monitoring** alerts for CPU/memory usage
- [ ] **Create deployment checklist** for configuration validation

### Short Term (Next Month)
- [ ] **Implement staging environment** with production-like configuration
- [ ] **Add integration tests** for schema validation
- [ ] **Create runbook** for common production issues
- [ ] **Add database migration validation** in CI/CD

### Long Term (Next Quarter)
- [ ] **Implement distributed tracing** for request debugging
- [ ] **Add automated schema validation** against database
- [ ] **Create infrastructure-as-code** for repeatable deployments
- [ ] **Implement canary deployments** to catch issues early

## Key Takeaways

1. **Complex issues require systematic debugging** - jumping between symptoms wastes time
2. **Good error messages are infrastructure** - invest in detailed logging/monitoring  
3. **Environment parity prevents surprises** - local should match production
4. **Resource constraints cause mysterious failures** - don't run production on development specs
5. **Schema validation is often overlooked** - database and API schemas must stay in sync

## Prevention Checklist

Before any production deployment:
- [ ] All environment variables documented and validated
- [ ] Resource limits tested under realistic load
- [ ] Database connectivity tested with exact production config
- [ ] Schema migrations include corresponding validation updates
- [ ] Error handling provides actionable debugging information
- [ ] Health checks cover all critical dependencies

---

**Total Resolution Time:** 3 hours  
**Primary Blocker:** Poor error visibility masked root causes  
**Most Effective Solution:** Systematic infrastructure debugging + improved error handling

*This retrospective should be reviewed during next sprint planning to ensure action items are prioritized appropriately.*
