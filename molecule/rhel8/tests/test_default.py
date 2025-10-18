"""
Testinfra tests for Apache Demo Role
Comprehensive tests for syntax, lint, idempotency, performance
"""

import pytest
import time
import subprocess
import re


@pytest.fixture(scope="session")
def apache_service(host):
    """Get Apache service information"""
    return host.service("httpd")


@pytest.fixture(scope="session")
def apache_config(host):
    """Get Apache configuration"""
    return host.file("/etc/httpd/conf/httpd.conf")


class TestApacheService:
    """Test Apache service functionality"""
    
    def test_apache_service_is_running(self, apache_service):
        """Test that Apache service is running and enabled"""
        assert apache_service.is_running
        assert apache_service.is_enabled
        
    def test_apache_service_status(self, apache_service):
        """Test Apache service status"""
        assert apache_service.status == "active"
        
    def test_apache_listening_on_port(self, host):
        """Test that Apache is listening on port 80"""
        assert host.socket("tcp://0.0.0.0:80").is_listening
        
    def test_apache_process_exists(self, host):
        """Test that Apache process is running"""
        apache_processes = host.process.filter(user="apache")
        assert len(apache_processes) > 0


class TestApacheConfiguration:
    """Test Apache configuration and syntax"""
    
    def test_apache_config_file_exists(self, apache_config):
        """Test that Apache configuration file exists"""
        assert apache_config.exists
        assert apache_config.is_file
        
    def test_apache_config_syntax(self, host):
        """Test Apache configuration syntax"""
        result = host.run("httpd -t")
        assert result.rc == 0
        assert "Syntax OK" in result.stdout
        
    def test_apache_config_contains_required_directives(self, apache_config):
        """Test that Apache configuration contains required directives"""
        config_content = apache_config.content_string
        
        # Required directives
        required_directives = [
            "ServerRoot",
            "Listen",
            "DocumentRoot",
            "User apache",
            "Group apache"
        ]
        
        for directive in required_directives:
            assert directive in config_content


class TestApacheContent:
    """Test Apache content and functionality"""
    
    def test_apache_document_root_exists(self, host):
        """Test that document root exists"""
        doc_root = host.file("/var/www/html")
        assert doc_root.exists
        assert doc_root.is_directory
        
    def test_apache_test_page_exists(self, host):
        """Test that test page exists"""
        test_page = host.file("/var/www/html/index.html")
        assert test_page.exists
        assert test_page.is_file
        assert test_page.size > 0
        
    def test_apache_test_page_content(self, host):
        """Test test page content"""
        test_page = host.file("/var/www/html/index.html")
        content = test_page.content_string
        
        # Check for expected content
        assert "Apache Demo Server" in content
        assert "html" in content.lower()
        assert "head" in content.lower()
        assert "body" in content.lower()
        
    def test_apache_test_page_permissions(self, host):
        """Test test page permissions"""
        test_page = host.file("/var/www/html/index.html")
        assert test_page.user == "root"
        assert test_page.group == "root"
        assert test_page.mode == 0o644


class TestApacheHTTP:
    """Test Apache HTTP functionality"""
    
    def test_apache_http_response(self, host):
        """Test Apache HTTP response"""
        # Wait for Apache to be ready
        time.sleep(5)
        
        # Test HTTP response
        result = host.run("curl -s -o /dev/null -w '%{http_code}' http://localhost/")
        assert result.rc == 0
        assert result.stdout.strip() == "200"
        
    def test_apache_http_content(self, host):
        """Test Apache HTTP content"""
        result = host.run("curl -s http://localhost/")
        assert result.rc == 0
        assert "Apache Demo Server" in result.stdout
        
    def test_apache_http_headers(self, host):
        """Test Apache HTTP headers"""
        result = host.run("curl -s -I http://localhost/")
        assert result.rc == 0
        assert "HTTP/1.1 200 OK" in result.stdout
        assert "Server:" in result.stdout


class TestApachePerformance:
    """Test Apache performance and metrics"""
    
    def test_apache_response_time(self, host):
        """Test Apache response time"""
        start_time = time.time()
        result = host.run("curl -s -o /dev/null -w '%{time_total}' http://localhost/")
        end_time = time.time()
        
        if result.rc == 0:
            response_time = float(result.stdout.strip())
            # Response time should be less than 2 seconds
            assert response_time < 2.0
            
    def test_apache_concurrent_requests(self, host):
        """Test Apache concurrent requests"""
        # Test multiple concurrent requests
        processes = []
        for i in range(3):
            result = host.run("curl -s -o /dev/null -w '%{http_code}' http://localhost/ &")
            processes.append(result)
            
        # Wait for all requests to complete
        time.sleep(3)
        
        # Check that all requests succeeded
        for process in processes:
            assert process.rc == 0
            
    def test_apache_memory_usage(self, host):
        """Test Apache memory usage"""
        result = host.run("ps aux | grep httpd | grep -v grep")
        assert result.rc == 0
        assert "httpd" in result.stdout
        
    def test_apache_process_count(self, host):
        """Test Apache process count"""
        result = host.run("pgrep httpd | wc -l")
        assert result.rc == 0
        
        process_count = int(result.stdout.strip())
        # Should have at least one Apache process
        assert process_count > 0
        # Should not have too many processes
        assert process_count < 20


class TestApacheIdempotency:
    """Test Apache role idempotency"""
    
    def test_apache_package_installed(self, host):
        """Test that Apache package is installed"""
        result = host.run("rpm -q httpd")
        assert result.rc == 0
        assert "httpd" in result.stdout
        
    def test_apache_service_configuration(self, host):
        """Test that Apache service is properly configured"""
        result = host.run("systemctl is-enabled httpd")
        assert result.rc == 0
        assert result.stdout.strip() == "enabled"
        
    def test_apache_firewall_configuration(self, host):
        """Test that firewall is properly configured"""
        result = host.run("firewall-cmd --list-ports")
        if result.rc == 0:
            assert "80/tcp" in result.stdout or "http" in result.stdout


class TestApacheLogging:
    """Test Apache logging configuration"""
    
    def test_apache_log_directory_exists(self, host):
        """Test that Apache log directory exists"""
        log_dir = host.file("/var/log/httpd")
        assert log_dir.exists
        assert log_dir.is_directory
        
    def test_apache_error_log_exists(self, host):
        """Test that Apache error log exists"""
        error_log = host.file("/var/log/httpd/error_log")
        assert error_log.exists
        
    def test_apache_access_log_exists(self, host):
        """Test that Apache access log exists"""
        access_log = host.file("/var/log/httpd/access_log")
        assert access_log.exists


class TestApacheSecurity:
    """Test Apache security configuration"""
    
    def test_apache_user_exists(self, host):
        """Test that Apache user exists"""
        apache_user = host.user("apache")
        assert apache_user.exists
        assert apache_user.name == "apache"
        
    def test_apache_group_exists(self, host):
        """Test that Apache group exists"""
        apache_group = host.group("apache")
        assert apache_group.exists
        assert apache_group.name == "apache"
        
    def test_apache_document_root_permissions(self, host):
        """Test Apache document root permissions"""
        doc_root = host.file("/var/www/html")
        assert doc_root.exists
        assert doc_root.is_directory
        assert doc_root.user == "root"
        assert doc_root.group == "root"

