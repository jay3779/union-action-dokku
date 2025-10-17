# Feature Specification: Dokku Deployment Provisioning

**Feature Branch**: `002-dokku-deploy`  
**Created**: 2024-12-19  
**Status**: Draft  
**Input**: User description: "provision @@union-action/ union-action to deploy to @Dokku"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Deploy Union Action API to Dokku (Priority: P1)

As a DevOps engineer, I want to deploy the Union Action FastAPI application to a Dokku server so that the workflow integration API is available for production use.

**Why this priority**: This is the core functionality - without deployment, the application cannot serve its intended purpose of providing workflow endpoints for the chatops-agent.

**Independent Test**: Can be fully tested by successfully deploying the application to a Dokku server and verifying all API endpoints are accessible and functional.

**Acceptance Scenarios**:

1. **Given** a Dokku server is available, **When** I provision the union-action application, **Then** the application deploys successfully and is accessible via HTTP
2. **Given** the application is deployed, **When** I access the health endpoint, **Then** I receive a healthy status response
3. **Given** the application is deployed, **When** I access the API documentation, **Then** I can view the available endpoints and their schemas

---

### User Story 2 - Configure Environment Variables (Priority: P2)

As a DevOps engineer, I want to configure environment variables for the deployed application so that it can integrate with external services like Typeform and OpenAI.

**Why this priority**: The application requires external service configuration to function properly in production, but the core deployment can work without these initially.

**Independent Test**: Can be tested by deploying with environment variables and verifying the application uses them correctly.

**Acceptance Scenarios**:

1. **Given** the application is deployed, **When** I set the TYPEFORM_API_TOKEN environment variable, **Then** the application can integrate with Typeform services
2. **Given** the application is deployed, **When** I set the OPENAI_API_KEY environment variable, **Then** the application can use OpenAI services
3. **Given** the application is deployed, **When** I configure logging environment variables, **Then** the application uses the specified log level and format

---

### User Story 3 - Ensure Application Health and Monitoring (Priority: P3)

As a DevOps engineer, I want to monitor the deployed application's health so that I can ensure it's running properly and troubleshoot issues.

**Why this priority**: Monitoring is important for production operations but the application can function without advanced monitoring initially.

**Independent Test**: Can be tested by checking health endpoints and verifying logs are accessible.

**Acceptance Scenarios**:

1. **Given** the application is deployed, **When** I check the health endpoint, **Then** I receive status information including version and timestamp
2. **Given** the application is deployed, **When** I examine the application logs, **Then** I can see structured logging output
3. **Given** the application is deployed, **When** the application encounters an error, **Then** errors are logged with appropriate detail

---

### Edge Cases

- What happens when the Dokku server is unavailable or unreachable?
- How does the system handle Docker build failures during deployment?
- What happens when required environment variables are missing?
- How does the system handle port conflicts on the Dokku server?
- What happens when the application fails to start after deployment?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST deploy the union-action FastAPI application to a Dokku server
- **FR-002**: System MUST configure the application to run on port 8000
- **FR-003**: System MUST set up environment variable configuration for external service integration
- **FR-004**: System MUST ensure the application health endpoint is accessible at `/health`
- **FR-005**: System MUST provide API documentation at `/docs` and `/redoc` endpoints
- **FR-006**: System MUST configure CORS to allow cross-origin requests from the chatops-agent
- **FR-007**: System MUST set up structured logging with configurable log levels
- **FR-008**: System MUST handle graceful startup and shutdown of the application
- **FR-009**: System MUST provide error handling and logging for deployment failures
- **FR-010**: System MUST support environment variable configuration for TYPEFORM_API_TOKEN, OPENAI_API_KEY, LOG_LEVEL, and LOG_FORMAT
- **FR-011**: System MUST run both union-action API and chatops-agent as separate processes within the same container
- **FR-012**: System MUST ensure chatops-agent can communicate with union-action API via localhost
- **FR-013**: System MUST use a process manager (supervisord/systemd) to manage both processes with automatic restart capabilities
- **FR-014**: System MUST ensure both processes start in the correct order (union-action API before chatops-agent)
- **FR-015**: System MUST implement health checks that verify both processes are running, with API endpoint as primary indicator
- **FR-016**: System MUST ensure health check fails if either process is not running
- **FR-017**: System MUST configure shared container resources with process-specific limits and priority
- **FR-018**: System MUST ensure union-action API has higher priority for resource allocation than chatops-agent
- **FR-019**: System MUST use Dokku's built-in logging system for both processes
- **FR-020**: System MUST ensure both processes write to standard output/error for Dokku log collection

### Key Entities

- **Deployment Configuration**: Represents the Dokku deployment settings including port mapping, environment variables, and health checks
- **Application Environment**: Represents the runtime environment configuration including external service tokens and logging settings

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Application deploys successfully to Dokku within 5 minutes of initiation
- **SC-002**: Health endpoint responds with status "healthy" within 2 seconds of request
- **SC-003**: API documentation is accessible and displays all available endpoints
- **SC-004**: Application handles 100 concurrent requests without performance degradation
- **SC-005**: Environment variables are properly configured and accessible to the application
- **SC-006**: Application logs are accessible through Dokku's logging system and include relevant operational information
- **SC-007**: Deployment process completes without manual intervention
- **SC-008**: Application remains stable and accessible for 24 hours after deployment

## Clarifications

### Session 2024-12-19

- Q: How should the chatops-agent integration be handled in the deployment? → A: Single container runs both union-action API and chatops-agent as separate processes
- Q: How should the two processes be managed within the container? → A: Use process manager (supervisord/systemd) to manage both processes with automatic restart
- Q: How should health checks be implemented for the multi-process container? → A: Health check verifies both processes are running, with API endpoint as primary indicator
- Q: How should resources be allocated between the two processes? → A: Shared container resources with process-specific limits and priority
- Q: How should logging be configured for the multi-process container? → A: Use Dokku's built-in logging without process-specific configuration

## Assumptions

- Dokku server is available and properly configured
- Docker is available on the Dokku server
- Network connectivity exists between deployment environment and Dokku server
- Required external services (Typeform, OpenAI) are available when their respective environment variables are configured
- The union-action application code is ready for production deployment
- Standard Dokku deployment practices and conventions will be followed
- Chatops-agent will be bundled within the union-action container as a separate process