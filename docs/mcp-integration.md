# Canvas MCP Integration

## Overview

The Canvas MCP (Model Context Protocol) server provides AI agents with access to Canvas LMS tools. The integration is designed for standalone operation, where the C1 agent connects directly to the Canvas MCP server.

## Architecture

```
┌─────────────────┐
│   C1 Agent      │ ← Configured separately in Thesys platform
└────────┬────────┘
         │
         │ MCP Protocol (stdio)
         │
┌────────▼────────┐
│  Canvas MCP     │
│  Server         │
└────────┬────────┘
         │
         │ Canvas API (HTTPS)
         │
┌────────▼────────┐
│  Canvas LMS     │
└─────────────────┘
```

## Canvas MCP Server

### Location
`/Users/najik/development/canvas-instructure-mcp`

### Running the Server

```bash
cd /Users/najik/development/canvas-instructure-mcp
source venv/bin/activate
python -m src.canvas_mcp
```

The server runs using **FastMCP 2.0** with **stdio transport**.

### Available Tools (9 total)

The Canvas MCP server provides these tools for AI agents:

1. **canvas_health_check** - Check Canvas API connection
2. **canvas_course_list** - List courses for current user
3. **canvas_course_get** - Get course details
4. **canvas_assignment_list** - List assignments for a course
5. **canvas_student_list** - List students in a course
6. **canvas_student_get** - Get student details with grades
7. **canvas_enrollments_list** - List course enrollments
8. **canvas_submissions_list** - List assignment submissions
9. **canvas_submission_get** - Get specific submission details

For detailed documentation on each tool, see `/Users/najik/development/canvas-instructure-mcp/README.md`

## Configuration

### Environment Variables

Canvas MCP server credentials are stored in the backend `.env`:

```env
# Canvas API Configuration (for MCP server)
CANVAS_API_URL=https://canvas.instructure.com/
CANVAS_API_KEY=7~cMYwXhmrh8AyrxECxFyK8FBLnwNDPfZCM3MkLJ2Fvn88TMMc9C6tkUNR86xWMR9Q
```

### MCP Configuration for Claude Code

For local development with Claude Code, the Canvas MCP is configured in `.mcp.json`:

```json
{
  "mcpServers": {
    "canvas-instructure": {
      "command": "python3",
      "args": ["-m", "src.canvas_mcp"],
      "cwd": "/Users/najik/development/canvas-instructure-mcp",
      "env": {
        "CANVAS_API_URL": "${CANVAS_API_URL}",
        "CANVAS_API_KEY": "${CANVAS_API_KEY}",
        "PYTHONPATH": "/Users/najik/development/canvas-instructure-mcp/src"
      }
    }
  }
}
```

**Note**: This `.mcp.json` configuration is for Claude Code IDE integration, not for the C1 agent.

## C1 Agent Integration

### Setting Up C1 Agent with Canvas MCP

When configuring your C1 agent in the Thesys platform:

1. **MCP Server Details**:
   - **Transport**: stdio
   - **Command**: `python3 -m src.canvas_mcp`
   - **Working Directory**: `/Users/najik/development/canvas-instructure-mcp`

2. **Environment Variables**:
   ```
   CANVAS_API_URL=https://canvas.instructure.com/
   CANVAS_API_KEY=<your-canvas-api-key>
   PYTHONPATH=/Users/najik/development/canvas-instructure-mcp/src
   ```

3. **Tool Discovery**:
   The C1 agent will automatically discover all 9 Canvas tools when it connects to the MCP server.

### Security Considerations

- Canvas API keys should be scoped to appropriate permissions
- Use teacher-specific API keys for production
- Consider token rotation policies
- The MCP server validates all API requests through Canvas LMS

## Testing the Integration

### 1. Test MCP Server Standalone

```bash
# Start the server
cd /Users/najik/development/canvas-instructure-mcp
source venv/bin/activate
CANVAS_API_URL="https://canvas.instructure.com/" \
CANVAS_API_KEY="your-key" \
python -m src.canvas_mcp

# Should see FastMCP 2.0 startup banner
# Server name: canvas-instructure-mcp
# Transport: STDIO
```

### 2. Test with Claude Code

Open Claude Code IDE and use Canvas MCP tools directly in the chat interface.

### 3. Test with C1 Agent

When your C1 agent is configured:
- Ask it to list your Canvas courses
- Request assignment details
- Query student submissions
- All Canvas operations will flow through the MCP server

## Troubleshooting

### Issue: MCP Server Won't Start

**Error**: `ValueError: CANVAS_API_URL and CANVAS_API_KEY environment variables must be set`

**Solution**: Ensure environment variables are set:
```bash
export CANVAS_API_URL="https://canvas.instructure.com/"
export CANVAS_API_KEY="your-key"
```

### Issue: Canvas API Connection Failed

**Error**: Canvas API returns 401 Unauthorized

**Solutions**:
1. Verify API key is valid and not expired
2. Check API URL has no trailing slashes except the final one
3. Test with curl:
   ```bash
   curl -H "Authorization: Bearer YOUR_KEY" \
        https://canvas.instructure.com/api/v1/users/self
   ```

### Issue: Tools Not Appearing in C1 Agent

**Solutions**:
1. Verify MCP server is running
2. Check C1 agent configuration has correct command/path
3. Ensure PYTHONPATH is set correctly
4. Review C1 agent logs for connection errors

## Current Status

### ✅ Completed (Epic 8 - Partial)

- [x] Canvas MCP server located and tested
- [x] MCP configuration created for Claude Code
- [x] Canvas API credentials configured
- [x] Server startup verified with FastMCP 2.0
- [x] All 9 Canvas tools available and documented

### 🔄 Pending (C1 Agent Configuration)

- [ ] Configure C1 agent in Thesys platform
- [ ] Connect C1 agent to Canvas MCP server
- [ ] Test end-to-end: C1 agent → Canvas MCP → Canvas LMS
- [ ] Production deployment configuration

**Note**: The C1 agent configuration is done separately in the Thesys platform, not in this backend codebase.

## Next Steps

The Canvas MCP integration is ready for use. The next phase is:

**Epic 9: Course Context Management** - Enable teachers to select and work with specific Canvas courses in conversation context.

## References

- Canvas MCP Server: `/Users/najik/development/canvas-instructure-mcp/README.md`
- Canvas MCP Testing Guide: `/Users/najik/development/canvas-instructure-mcp/TESTING.md`
- FastMCP Documentation: https://gofastmcp.com
- Thesys C1 Documentation: https://docs.thesys.dev
