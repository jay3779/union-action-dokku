# xsrc Integration Guide

**Date**: October 13, 2025  
**Status**: Live Typeform supported (when token present); Stub fallback remains for MVP

---

## Overview

The WhatsApp ChatOps Agent integrates `xunion-action-integration/xsrc` as a **local Python library** (not a separate HTTP API service). This eliminates network overhead, simplifies deployment, and enables rapid iteration.

### What is xsrc?

`xsrc` is a transformation pipeline library that provides:
1. **Domain Models**: Pydantic models for NHS complaints, ethical analysis, and survey deployment
2. **Adapters**: Transformations between pipeline stages (Complaint→Kantian, Kantian→KOERS)
3. **Services**: Kantian ethical analyzer, Typeform live client, and CareVoice stub

---

## Architecture Decisions

### 1. Local Library vs. HTTP API

**Decision**: Direct Python imports instead of HTTP calls

**Rationale**:
- Both components in same monorepo
- No network latency
- Simpler error handling
- Easier debugging
- Lower deployment cost (one service vs. two)

**Implementation**:
```python
# whatsapp-chatops-agent/src/union_action_client.py
import sys
from pathlib import Path

xsrc_path = Path(__file__).parent.parent.parent / "xunion-action-integration"
sys.path.insert(0, str(xsrc_path))

from xsrc.models import NHSComplaintDocument, EthicalAnalysisReport
from xsrc.services.kantian_analyzer import KantianEthicalAnalyzer
```

### 2. Single Unified Service Deployment

**Decision**: Deploy as one service on Render

**Rationale**:
- Render builds from `whatsapp-chatops-agent/` directory
- xsrc accessible via `../xunion-action-integration`
- Shared Python runtime
- Shared logging configuration
- Lower cost

**render.yaml**:
```yaml
services:
  - type: web
    rootDir: whatsapp-chatops-agent  # Service root
    buildCommand: |
      pip install -r requirements.txt
      python -c "import sys; from pathlib import Path; xsrc_path = Path('../xunion-action-integration'); sys.path.insert(0, str(xsrc_path)); from xsrc.models import NHSComplaintDocument; print('✓ xsrc import successful')"
```

---

## Pipeline Flow

### Step-by-Step Transformation

**Input**: WhatsApp complaint text  
**Output**: Ethical analysis report + KOERS survey URL

```
1. complaint_text (str)
   "I was denied training despite requesting it."
   
2. _mock_complaint_document()
   → NHSComplaintDocument
   {
     "narrative": "I was denied training...",
     "pentadic_context": {...},
     "maxim_extraction": "...",
     "rhetorical_context": {...}
   }
   
3. ComplaintToKantianAdapter.transform()
   → CaseBuilder input (dict)
   {
     "maxim": "Training can be denied when convenient",
     "scene": {"phenomenal_constraints": "...", "noumenal_duties": "..."},
     "agent": {"role": "Employee"},
     "action": {"description": "..."}
   }
   
4. KantianEthicalAnalyzer.analyze()
   → EthicalAnalysisReport
   {
     "universalizability_test": {"verdict": "FAILURE", "rationale": "..."},
     "humanity_formula_test": {"verdict": "VIOLATION", "rationale": "..."},
     "autonomy_test": {"verdict": "VIOLATION", "rationale": "..."},
     "procedural_justice_test": {"verdict": "FAILURE", "rationale": "..."},
     "summary": "Systematic ethical failure requiring remediation"
   }
   
5. KantianToKOERSAdapter.transform()
   → DeploymentReport
  {
    "survey_url": "https://typeform.com/to/<FORM_ID>",
    "module_list": ["core", "categorical_imperative", "dignity_instrumentalization", "autonomy_agency"],
    "item_count": 22
  }
```

---

## Typeform Integration Modes

**Live Mode (Production)**
- Enabled automatically when `TYPEFORM_API_TOKEN` is set
- Uses `xsrc/services/typeform_live.py` to create real Typeform forms via API
- Requires a Typeform Personal Access Token with `forms:write` scope
- Returns a real share URL `https://typeform.com/to/<FORM_ID>`

**Stub Mode (MVP/Dev)**
- Used when `TYPEFORM_API_TOKEN` is not set and CareVoice library is unavailable
- Uses `xsrc/services/carevoice_stub.py` and logs `carevoice_stub_used`
- Returns a mock URL (`https://typeform.com/to/MOCK_...`)

## MVP Limitations

### 1. Mock NHSComplaintDocument Parsing

**Current**: Generic pentadic structure

```python
def _mock_complaint_document(self, complaint_text: str) -> NHSComplaintDocument:
    return NHSComplaintDocument(
        narrative=complaint_text,
        pentadic_context={
            "act": "Organizational action described in complaint",
            "scene": {
                "phenomenal": "Workplace constraints",
                "noumenal": "Professional ethics duties"
            },
            "agent": {"role": "Employee"},
            ...
        },
        maxim_extraction="[Generic maxim - TODO: Real extraction]",
        ...
    )
```

**Production TODO**: Implement NLP extraction of Burke's Pentad elements from raw text:
- **Act**: What happened (extract from narrative)
- **Scene**: Context (phenomenal vs. noumenal)
- **Agent**: Who (extract role/position)
- **Agency**: How (extract method/mechanism)
- **Purpose**: Why (extract stated/implied goal)
- **Maxim**: Organizational principle (extract or infer)

### 2. CareVoice Stub

**Current (Dev)**: Stub Typeform URL generation when token missing

```python
# xsrc/services/carevoice_stub.py
def deploy_survey(...) -> Dict[str, Any]:
    logger.warning("carevoice_stub_used", message="NOT PRODUCTION READY")
    return {
        "survey_id": f"mock_tf_{hash(...)}",
        "survey_url": f"https://typeform.com/to/MOCK_{...}",
        ...
    }
```

**Production Note**: Live Typeform integration is available via `typeform_live.py`.
You may still integrate the official CareVoice library for template management,
response collection, and validation if desired.

### 3. Kantian Analysis Heuristics

**Current**: Keyword-based detection

```python
# xsrc/services/kantian_analyzer.py
non_universalizable_keywords = ["convenient", "optional", "discretionary", ...]
dignity_violation_keywords = ["denied", "refused", "rejected", ...]
```

**Production TODO**: Enhanced analysis:
- AI-powered reasoning (GPT-4, Claude)
- Contextual understanding
- Nuanced moral assessment
- Case law / precedent integration

---

## Testing Strategy

### Unit Tests

**Domain Models** (`tests/unit/test_domain_models.py`):
- Pydantic validation
- Required fields
- Type checking
- Invalid inputs

**Kantian Analyzer** (`tests/unit/test_kantian_analyzer.py`):
- Each ethical test individually
- Verdict detection
- Rationale generation
- Edge cases

**Adapters** (`tests/unit/test_adapters.py`):
- Transformation logic
- Field mapping
- Validation failures

### Integration Tests

**Local Pipeline** (`tests/integration/test_local_pipeline.py`):
- escalate_to_ethics() end-to-end
- generate_koers_survey() end-to-end
- Full pipeline (complaint → survey)

**Webhook** (`tests/integration/test_webhook_with_local_pipeline.py`):
- Webhook payload → pipeline → response
- Error handling
- Multiple violations detection

---

## Troubleshooting

### ImportError: No module named 'xsrc'

**Cause**: xsrc path not added to sys.path correctly

**Fix**:
```python
# Verify path exists
xsrc_path = Path(__file__).parent.parent.parent / "xunion-action-integration"
print(f"xsrc path exists: {xsrc_path.exists()}")
print(f"xsrc path: {xsrc_path.absolute()}")

# Check directory structure
ls -la ../xunion-action-integration/xsrc/
```

### CareVoice stub warning in logs

**Expected**: MVP uses carevoice_stub.py, not production CareVoice

**Log Message**:
```
carevoice_stub_used: Using mock CareVoice deployment - NOT PRODUCTION READY
```

**Action**: Monitor logs for this warning. Replace stub before production launch.

### Kantian analysis returns same verdict every time

**Cause**: Keyword-based heuristics are simplistic

**Fix**: Review heuristics in `xsrc/services/kantian_analyzer.py`:
- Adjust keyword lists
- Add context analysis
- Consider AI integration

---

## Production Checklist

- [ ] **NLP Parsing**: Implement real Burke's Pentad extraction
- [ ] **CareVoice Integration**: Replace stub with actual library
- [ ] **Typeform API**: Add real API credentials
- [ ] **Kantian Analysis**: Enhance with AI reasoning
- [ ] **Testing**: Add contract tests for xsrc boundaries
- [ ] **Monitoring**: Add xsrc-specific metrics
- [ ] **Documentation**: Update with production examples
- [ ] **Performance**: Benchmark transformation pipeline
- [ ] **Error Handling**: Add xsrc-specific error recovery
- [ ] **Logging**: Enhance xsrc diagnostic logging

---

## References

- [xsrc Models](../../../xunion-action-integration/xsrc/models/)
- [xsrc Adapters](../../../xunion-action-integration/xsrc/adapters/)
- [xsrc Services](../../../xunion-action-integration/xsrc/services/)
- [Kantian Analyzer Implementation](../../../xunion-action-integration/xsrc/services/kantian_analyzer.py)
- [CareVoice Stub](../../../xunion-action-integration/xsrc/services/carevoice_stub.py)

