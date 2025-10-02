# Omega Module Cleanup - DEPRECATED Files

**Date**: 2025-10-02  
**Action**: Cleanup Phase 0 - Removing unused/obsolete files  

## Files DELETED (Not Used Anywhere)

### 1. `market.py` (41 lines)
**Reason**: Internal market matching (needs/offers) not used  
**Status**: DELETED  
**Migration**: N/A (feature not active)

### 2. `game.py` (3 lines)
**Reason**: Single EMA function, trivial  
**Status**: DELETED  
**Migration**: Use numpy.convolve or implement inline if needed

### 3. `zero_consciousness.py` (10 lines)
**Reason**: SPI proxy for consciousness, not used  
**Status**: DELETED  
**Migration**: Concept interesting but not integrated. If needed, implement in SR-Ω∞

### 4. `neural_chain.py` (32 lines)
**Reason**: Mini ledger, obsolete (we have worm_ledger_complete.py)  
**Status**: DELETED  
**Migration**: Use `penin.ledger.worm_ledger_complete.WORMLedger` instead

### 5. `checkpoint.py` (check usage first)
**Reason**: Simple checkpoint save/load
**Status**: TO INVESTIGATE  

### 6. `darwin_audit.py` (check usage first)
**Reason**: Very small file
**Status**: TO INVESTIGATE  

## Files CONSOLIDATED (Canonical Sources Exist)

### 7. `caos.py` (46 lines) - KEPT
**Reason**: Re-export from core/caos.py for backward compatibility  
**Status**: KEPT as compatibility layer  
**Canonical**: `penin.core.caos`

## Files TO REVIEW

### Large files that might have duplications:
- `sr.py` (1,157 lines) - vs `penin.sr.sr_service.py`
- `ethics_metrics.py` (958 lines) - vs `penin.ethics`
- `ledger.py` (801 lines) - vs `penin.ledger.worm_ledger_complete.py`
- `guards.py` (764 lines) - vs `penin.guard.sigma_guard_complete.py`

## Cleanup Summary

**Before**:
- 29 files in omega/
- 7,466 lines total
- Many obsolete/duplicate files

**After Cleanup**:
- TBD files
- TBD lines
- Clear canonical sources
