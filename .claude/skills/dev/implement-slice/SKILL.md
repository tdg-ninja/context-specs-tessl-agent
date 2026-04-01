---
name: implement-slice
description: Transform structured specification documents into working code through phased implementation planning. Use when implementing a spec, turning specifications into code, or when the user wants to convert a spec document into a temporal implementation plan with phases, dependencies, testing strategy, and observability.
---

# Spec to Implementation Plan

You are given a specification file that defines the intent of the feature. Your job is to turn that intent into a temporal, phased implementation plan that the user can review and approve before actual implementation begins.

## Core Guidelines

1. **Ask questions and be interactive** - Look for scenarios missed in the specification or confusing requirements. Clarify intent and validate assumptions.
2. **Research the codebase first** - Explore codebase to understand existing patterns, architectures, and dependencies before planning.
3. **Do not jump to code** - Create a detailed implementation plan broken down into temporal phases. Show what depends on what.
4. **Present plan for approval** - Always get user approval on the full phased implementation plan before implementing.


## Implementation Planning Best Practices

These patterns help create clear, temporal implementation plans that ensure all critical concerns are addressed.

### 1. Temporal Phase Ordering

Think through implementation in logical layers. While you can adapt the order based on feature needs, ensure all relevant phases are considered:

**Common phase ordering:**
1. **Types/Contracts** - Define interfaces, schemas, data structures first
2. **Domain Logic** - Core business logic and validation
3. **Persistence** - Database operations, queries, data access
4. **API Layer** - HTTP handlers, endpoints, request/response mapping
5. **UI Components** - Frontend components that consume the API

**Example - Feature: Course Enrollment**
```markdown
## Phase 1: Types & Contracts
- Define `EnrollmentEntity` for DynamoDB
- Define `EnrollmentRequest` and `EnrollmentResponse` types
- Update Student type to include `enrolledCourses: string[]`

↓ (Phase 2 depends on Phase 1 types)

## Phase 2: Domain Logic
- Create `enrollStudent()` function with validation:
  - Check if student already enrolled
  - Verify course exists
  - Check enrollment capacity
- Return typed result

↓ (Phase 3 depends on Phase 2 logic)

## Phase 3: Persistence
- Create `saveEnrollment()` DynamoDB operation
- Add GSI query for "get enrollments by student"
- Transaction: Update Student.enrolledCourses + Create EnrollmentEntity

↓ (Phase 4 depends on Phase 3 persistence)

## Phase 4: API Endpoints
- POST /api/enroll endpoint
- GET /api/students/:id/enrollments endpoint
- Error handling: 400 (already enrolled), 404 (course not found)
```

**When to reorder:** If adding a feature to existing domain logic, you might start with persistence changes, then update domain, then types. Always justify the ordering.

### 2. Observability - Logs That Prove Behavior

Define what to log, when, and why. Logs should prove your system is behaving correctly and help debug when it's not.

**DO ✅ - Structured logs with context**
```typescript
// Log business events with context
logger.info('Student enrolled in course', {
  studentId,
  courseId,
  enrollmentId,
  timestamp: new Date().toISOString()
});

// Log validation failures for debugging
logger.warn('Enrollment rejected - already enrolled', {
  studentId,
  courseId,
  attemptedAt: new Date().toISOString()
});

// Log errors with full context
logger.error('Failed to save enrollment', {
  error: err.message,
  stack: err.stack,
  studentId,
  courseId
});
```

**DON'T ❌ - Logs without context**
```typescript
logger.info('Enrollment successful');  // Which student? Which course?
logger.error('Database error');         // What operation failed?
```

**Observability proves system behavior:**
- Success logs prove happy path works
- Warning logs prove validation is enforcing rules
- Error logs prove failures are caught and handled
- Include correlation IDs to trace requests across services

### 3. Cross-Cutting Concerns

Address these architectural concerns in your plan when relevant:

**Idempotency & Retry-Safety**
```markdown
## Idempotency Strategy
- POST /api/enroll: Use idempotency key (studentId + courseId)
- Check if enrollment exists before creating → Return 200 if already enrolled
- DynamoDB conditional writes: "only create if not exists"
```

**Rate Limiting (when needed)**
```markdown
## Rate Limiting
- Limit enrollment API to 10 requests/minute per student
- Use API Gateway throttling or in-memory rate limiter
```

**Error Handling Patterns**
```markdown
## Error Handling
- 400: Invalid request (missing fields, invalid format)
- 404: Resource not found (student or course doesn't exist)
- 409: Conflict (already enrolled, course full)
- 500: Server errors (database unavailable, unexpected errors)
```

**Security Considerations**
```markdown
## Security
- Dont propose code that is prone to SQL injection, etc.
- Sanitize data before returning to client
```

### 4. Testing Strategy - Categories & Test Names

Define test categories and list specific test names. This proves comprehensive coverage without writing actual test code.

**Example:**
```markdown
## Testing Strategy

### Unit Tests (5 tests)
**File:** `backend/src/features/enrollment/enrollment.service.test.ts`
1. `enrollStudent_success_createsEnrollment`
2. `enrollStudent_alreadyEnrolled_returnsConflict`
3. `enrollStudent_courseNotFound_throwsError`
4. `enrollStudent_courseFull_throwsError`
5. `calculateEnrollmentCount_returnsCorrectCount`

### Integration Tests (3 tests)
**File:** `backend/src/features/enrollment/enrollment.api.test.ts`
1. `POST_/api/enroll_validRequest_returns201`
2. `POST_/api/enroll_duplicateEnrollment_returns200Idempotent`
3. `GET_/api/students/:id/enrollments_returnsEnrollmentsList`

```

**Why categorize:** Unit tests validate business logic in isolation. Integration tests validate API contracts and database operations. 


### 5. New Libraries (Only When Needed)

Only include this section if new dependencies are required. If using existing libraries, skip this section.

**Example when needed:**
```markdown
## New Libraries Required

### `zod` (v3.22.0)
**Why:** Runtime request validation for enrollment API
**Usage:** Define EnrollmentRequestSchema, validate req.body before processing
**Alternative considered:** Manual validation (rejected - error-prone)

### `uuid` (v9.0.0)
**Why:** Generate unique enrollment IDs
**Usage:** `enrollmentId = uuidv4()`
```
---

## Plan Presentation Format

Present your plan to the user in this structure:

```markdown
# Implementation Plan: [Feature Name]

## Phases

### Phase 1: [Name]
**What:** ...
**Why:** ...
**Dependencies:** None / Depends on Phase X
**Changes:**
- File: path/to/file.ts - What changes
- File: path/to/new-file.ts - NEW: What it does

### Phase 2: [Name]
...

## Observability
- What logs prove system behavior
- Log examples with context

## Cross-Cutting Concerns
- Idempotency strategy (if applicable)
- Error handling approach
- Security considerations

## Testing Strategy
- Unit tests: N tests listed
- Integration tests: N tests listed

## New Libraries (if any)
- Library name, version, why, usage

## Summary of Changes
- File being Created | Edit | Deleted
- Very short sentence of Why the change per file
E.g.
 Files Affected Summary

 | File                                               | Action           | Why                                   |
 |----------------------------------------------------|------------------|---------------------------------------|
 | frontend/components/layout/AuthenticatedHeader.tsx | CREATE           | New unified header component          |
 | frontend/app/dashboard/page.tsx                    | EDIT             | Use AuthenticatedHeader               |
 | frontend/components/dashboard/DashboardContent.tsx | EDIT             | Remove user profile card              |
 | frontend/components/course/CourseHeader.tsx        | DELETE           | Replaced by AuthenticatedHeader       |



## Questions for User
- Any clarifications needed before implementation
```