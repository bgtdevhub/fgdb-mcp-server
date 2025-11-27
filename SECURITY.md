# Security Policy

## Supported Versions

We actively support and provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of the FGDB MCP Server seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

1. **Email**: Send an email to the project maintainers (contact information available in the repository)
2. **Private Security Advisory**: Use GitHub's private security advisory feature if you have access
3. **Direct Contact**: Contact the repository maintainers directly through their GitHub profiles

### What to Include

When reporting a vulnerability, please include:

- **Description**: A clear description of the vulnerability
- **Impact**: The potential impact of the vulnerability
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Proof of Concept**: If possible, include a proof of concept or exploit code (in a safe, non-destructive manner)
- **Suggested Fix**: If you have ideas on how to fix the issue, please share them

### What to Expect

- **Acknowledgment**: You will receive an acknowledgment within 48 hours
- **Initial Assessment**: We will provide an initial assessment within 7 days
- **Updates**: We will keep you informed of our progress
- **Resolution**: We will work to resolve the issue as quickly as possible

### Disclosure Policy

- We will work with you to understand and resolve the issue quickly
- We will credit you for the discovery (unless you prefer to remain anonymous)
- We will not disclose the vulnerability publicly until a fix is available
- We will coordinate with you on the timing of public disclosure

## Security Best Practices

### For Users

1. **Keep Dependencies Updated**: Regularly update your dependencies to receive security patches
2. **Use Environment Variables**: Store sensitive configuration in environment variables, not in code
3. **Limit Access**: Restrict access to geodatabases and use appropriate file permissions
4. **Monitor Logs**: Regularly review logs for suspicious activity
5. **Validate Input**: Always validate input from external sources

### For Developers

1. **Input Validation**: Always validate and sanitize user input
2. **SQL Injection Prevention**: Use parameterized queries and validate WHERE clauses
3. **Path Validation**: Validate file paths to prevent directory traversal attacks
4. **Error Handling**: Don't expose sensitive information in error messages
5. **Dependencies**: Keep dependencies updated and review security advisories

## Known Security Considerations

### Current Security Features

- **Input Validation**: All user inputs are validated before processing
- **SQL Injection Protection**: WHERE clauses are validated to prevent SQL injection
- **Path Validation**: File paths are validated to prevent directory traversal
- **Confirmation System**: High-risk operations require explicit user confirmation
- **Error Handling**: Errors are logged without exposing sensitive information

### Security Considerations

- **ArcPy Dependencies**: The project depends on ArcPy, which is provided by ArcGIS Pro
- **File System Access**: The server requires file system access to geodatabases
- **Network Security**: When used with MCP clients, ensure secure network connections
- **Authentication**: The server does not provide authentication - this should be handled by the MCP client or network layer

## Security Updates

Security updates will be:

- Released as patch versions (e.g., 0.1.1, 0.1.2)
- Documented in the release notes
- Tagged with security labels in the repository
- Announced through appropriate channels

## Security Contact

For security-related questions or concerns, please contact the project maintainers through the methods described in the [Reporting a Vulnerability](#reporting-a-vulnerability) section.

## Acknowledgments

We thank all security researchers and contributors who help keep this project secure. Your efforts are greatly appreciated.

