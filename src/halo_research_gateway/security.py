from dataclasses import dataclass
from ipaddress import ip_address, IPv4Address, IPv6Address
import re
import urllib.parse

# Error codes for different validation failures
UNSAFE_URL = "unsafe_url"
SCHEME = f"{UNSAFE_URL}/scheme"
USERINFO = f"{UNSAFE_URL}/userinfo"
PORT = f"{UNSAFE_URL}/port"
LENGTH = f"{UNSAFE_URL}/length"
HOST = f"{UNSAFE_URL}/host"
IP = f"{UNSAFE_URL}/ip"
DNS = f"{UNSAFE_URL}/dns"

@dataclass
class ParsedTarget:
    scheme: str
    host: str
    port: int | None
    path_query: str

class UrlPolicyError(Exception):
    def __init__(self, code: str, message: str = ""):
        self.code = code
        super().__init__(message)

def validate_url(url: str) -> ParsedTarget:
    if len(url) > 2000:
        raise UrlPolicyError(LENGTH, "URL exceeds maximum length of 2000 characters")
    
    parsed = urllib.parse.urlparse(url)
    
    # Only allow http/https schemes
    if parsed.scheme not in ('http', 'https'):
        raise UrlPolicyError(SCHEME, f"Invalid scheme: {parsed.scheme}")
        
    # Reject userinfo (username/password) in URLs
    if parsed.username or parsed.password:
        raise UrlPolicyError(USERINFO, "URL contains userinfo")
    
    # Check port - only allow 80/443 explicitly or no port
    if parsed.port is not None and parsed.port not in (80, 443):
        raise UrlPolicyError(PORT, f"Invalid port: {parsed.port}")
        
    # Missing host check 
    if not parsed.hostname:
        raise UrlPolicyError(HOST, "URL missing hostname")
    
    # Reject localhost and .local domains
    if parsed.hostname == 'localhost' or parsed.hostname.endswith('.local'):
        raise UrlPolicyError(HOST, f"Invalid hostname: {parsed.hostname}")
        
    # Handle special IP address encodings that should be rejected 
    # Check for decimal IPv4 encoding (2130706433 = 0x7f000001 = 127.0.0.1)
    try:
        if parsed.hostname.replace('.', '').isdigit() and len(parsed.hostname.split('.')) == 1:
            # This might be a decimal encoded IP address
            decimal_val = int(parsed.hostname)
            # Check for common loopback/invalid encodings
            if decimal_val in (2130706433, 0x7f000001, 0o17700000001):  # 127.0.0.1
                raise UrlPolicyError(IP, f"Invalid IP address: {parsed.hostname}")
    except ValueError:
        pass
    
    # Check for octal/hex encodings that could represent invalid IPs  
    if parsed.hostname.startswith('0') and len(parsed.hostname) > 1:
        try:
            # Try to parse as octal or hex
            if parsed.hostname.startswith('0x'):
                val = int(parsed.hostname, 16)
            elif parsed.hostname.startswith('0') and all(c in '01234567' for c in parsed.hostname[1:]):
                val = int(parsed.hostname, 8) 
            else:
                # Try decimal
                val = int(parsed.hostname)
            
            if val in (2130706433, 0x7f000001, 0o17700000001):  # 127.0.0.1  
                raise UrlPolicyError(IP, f"Invalid IP address: {parsed.hostname}")
        except ValueError:
            pass
    
    is_ip_literal = False
    if parsed.hostname.startswith('[') and parsed.hostname.endswith(']'):
        # IPv6 address - remove brackets for validation
        ip_str = parsed.hostname[1:-1]
        try:
            addr = ip_address(ip_str)
            if not classify_ip(addr):
                raise UrlPolicyError(IP, f"Invalid IP address: {ip_str}")
            is_ip_literal = True
        except ValueError:
            raise UrlPolicyError(HOST, "Invalid IPv6 address")
    elif parsed.hostname.replace('.', '').isdigit():
        # IPv4 address
        try:
            addr = ip_address(parsed.hostname)
            if not classify_ip(addr):
                raise UrlPolicyError(IP, f"Invalid IP address: {parsed.hostname}")
            is_ip_literal = True
        except ValueError:
            raise UrlPolicyError(HOST, "Invalid IPv4 address")
    
    # For non-IP literal hostnames, check for single-label hostnames (no dots) and reject them 
    if not is_ip_literal and '.' not in parsed.hostname:
        raise UrlPolicyError(HOST, "Single-label hostname not allowed")
    
    return ParsedTarget(
        scheme=parsed.scheme,
        host=parsed.hostname,
        port=parsed.port,
        path_query=urllib.parse.urlunparse(('', '', parsed.path, parsed.params, parsed.query, parsed.fragment))
    )

def classify_ip(ip) -> bool:
    """Classify IP addresses as public or not. Only allow public IPs."""
    try:
        addr = ip_address(ip)
        # Reject loopback, private, link-local, multicast, unspecified, reserved
        if isinstance(addr, IPv4Address):
            return (
                not addr.is_loopback and 
                not addr.is_private and 
                not addr.is_link_local and 
                not addr.is_multicast and 
                not addr.is_unspecified and 
                not addr.is_reserved
            )
        elif isinstance(addr, IPv6Address):
            return (
                not addr.is_loopback and 
                not addr.is_private and 
                not addr.is_link_local and 
                not addr.is_multicast and 
                not addr.is_unspecified and 
                not addr.is_reserved and
                not addr.is_unique_local  # Unique local addresses (fc00::/7)
            )
    except ValueError:
        return False

def validate_resolved(target: ParsedTarget, addresses) -> str:
    """Validate resolved IP addresses"""
    if not addresses:
        raise UrlPolicyError(DNS, "No DNS resolution")
        
    for addr in addresses:
        # Check if address is public
        if classify_ip(addr):
            return str(addr)
    
    raise UrlPolicyError(DNS, "All resolved addresses are non-public")

def validate_redirect(current: ParsedTarget, location: str) -> ParsedTarget:
    """Validate redirect URL by resolving relative paths"""
    # Parse the current URL for base
    base_url = f"{current.scheme}://{current.host}"
    if current.port is not None and current.port not in (80, 443):
        base_url += f":{current.port}"
    
    # Resolve the redirect location against the current URL
    absolute_url = urllib.parse.urljoin(base_url, location)
    
    return validate_url(absolute_url)

def is_sensitive_url(url: str) -> bool:
    """Check if URL contains sensitive parameters"""
    parsed = urllib.parse.urlparse(url)
    
    # Check for userinfo in URL
    if parsed.username or parsed.password:
        return True
        
    # Check query parameters for sensitive names (case-insensitive)
    query_params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    
    sensitive_names = [
        'token', 'key', 'secret', 'signature', 'sig', 
        'credential', 'auth', 'code', 'session', 'jwt'
    ]
    
    for param_name in query_params:
        if any(sens.lower() in param_name.lower() for sens in sensitive_names):
            return True
    
    return False