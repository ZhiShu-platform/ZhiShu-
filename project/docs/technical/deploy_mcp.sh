manager = MCPServerManager('${PROJECT_DIR}/mcp_servers.yaml')
print('MCP server configuration created at mcp_servers.yaml')
"
    
    log_info "MCP configuration created successfully"
}

# Start MCP servers
start_mcp_servers() {
    log_info "Starting MCP servers..."
    
    cd "${PROJECT_DIR}"
    
    # Start server manager
    python -m src.MCP.server_manager --config mcp_servers.yaml --action start &
    local manager_pid=$!
    
    log_info "MCP Server Manager started (PID: ${manager_pid})"
    
    # Wait a moment for servers to start
    sleep 5
    
    # Check server status
    python -m src.MCP.server_manager --config mcp_servers.yaml --action status
    
    log_info "MCP servers startup complete"
    log_info "Use 'python -m src.MCP.server_manager --action status' to check server status"
    log_info "Use 'npx @modelcontextprotocol/inspector' for debugging"
}

# Create systemd service (optional)
create_systemd_service() {
    if [[ "$1" == "--systemd" ]]; then
        log_info "Creating systemd service..."
        
        cat > "/tmp/emergency-mcp.service" << EOF
[Unit]
Description=Emergency Management MCP Servers
After=network.target

[Service]
Type=simple
User=${DEPLOY_USER}
WorkingDirectory=${PROJECT_DIR}
Environment=PATH=${PATH}
Environment=CONDA_DEFAULT_ENV=${PYTHON_ENV_NAME:-base}
ExecStart=/usr/bin/python -m src.MCP.server_manager --config mcp_servers.yaml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        log_info "Systemd service file created at /tmp/emergency-mcp.service"
        log_info "To install: sudo cp /tmp/emergency-mcp.service /etc/systemd/system/"
        log_info "To enable: sudo systemctl enable emergency-mcp.service"
        log_info "To start: sudo systemctl start emergency-mcp.service"
    fi
}

# Main deployment function
main() {
    log_info "Starting MCP deployment for Emergency Management System"
    log_info "Project directory: ${PROJECT_DIR}"
    
    check_deployment_host
    setup_environment
    check_model_installations
    check_python_environment
    install_mcp_dependencies # 此处会跳过安装步骤
    create_mcp_config
    start_mcp_servers
    create_systemd_service "$1"
    
    log_info "MCP deployment completed successfully!"
    log_info ""
    log_info "Next steps:"
    log_info "1. Check server status: python -m src.MCP.server_manager --action status"
    log_info "2. Test with MCP Inspector: npx @modelcontextprotocol/inspector"
    log_info "3. View debug guide: cat debug_mcp.md"
    log_info "4. Check logs in /var/log/emergency_management/"
}

# Run main function with all arguments
main "$@"
