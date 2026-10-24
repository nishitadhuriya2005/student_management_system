// Student Management System Configuration
// When deploying to AWS, replace the apiUrl with your deployed API Gateway Invoke URL.
// Example: "https://abcdef1234.execute-api.us-east-1.amazonaws.com"

window.APP_CONFIG = {
    // Default API URL:
    // If empty or set to auto, it checks window.location for local server,
    // or falls back to localStorage or AWS configured URL.
    apiUrl: window.localStorage.getItem('sms_api_url') || 'https://pw4h9vb0k3.execute-api.us-east-1.amazonaws.com',
    
    // AWS Region for reference
    awsRegion: 'us-east-1',
    
    // Default mock fallback if neither server nor API Gateway is reachable
    enableLocalFallback: true
};
