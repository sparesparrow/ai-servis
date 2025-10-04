#!/usr/bin/env python3
import boto3
import sys

def check_and_update_certificate(domain):
    """Check if domain has valid certificate, create if needed"""
    
    acm = boto3.client('acm', region_name='us-east-1')  # CloudFront vyžaduje us-east-1
    
    try:
        # List existing certificates
        response = acm.list_certificates(CertificateStatuses=['ISSUED'])
        
        for cert in response['CertificateSummaryList']:
            if domain in cert.get('DomainName', '') or domain in cert.get('SubjectAlternativeNames', []):
                print(f"✅ Certificate exists for {domain}: {cert['CertificateArn']}")
                return cert['CertificateArn']
        
        # Create new certificate if not exists
        print(f"🔧 Creating new certificate for {domain}")
        response = acm.request_certificate(
            DomainName=domain,
            ValidationMethod='DNS',
            SubjectAlternativeNames=[f'*.{domain}']
        )
        
        certificate_arn = response['CertificateArn']
        print(f"📋 New certificate requested: {certificate_arn}")
        print(f"⚠️  Don't forget to validate DNS records in ACM console!")
        
        return certificate_arn
        
    except Exception as e:
        print(f"❌ Error managing certificate for {domain}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_and_update_certificates.py <domain>")
        sys.exit(1)
    
    domain = sys.argv[1]
    check_and_update_certificate(domain)
