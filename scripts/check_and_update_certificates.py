#!/usr/bin/env python3
import boto3
import sys

def check_and_update_certificate(domain='ai.sparetools.dev'):
    """Check if domain has valid certificate, create if needed"""
    
    acm = boto3.client('acm', region_name='us-east-1')  # CloudFront requires us-east-1
    
    try:
        # List existing certificates
        response = acm.list_certificates(CertificateStatuses=['ISSUED'])
        
        for cert in response['CertificateSummaryList']:
            domain_name = cert.get('DomainName', '')
            alt_names = cert.get('SubjectAlternativeNames', [])
            
            if domain in domain_name or domain in alt_names:
                print(f"✅ Certificate exists for {domain}: {cert['CertificateArn']}")
                return cert['CertificateArn']
        
        # Create new certificate if not exists
        print(f"🔧 Creating new certificate for {domain}")
        response = acm.request_certificate(
            DomainName=domain,
            ValidationMethod='DNS'
        )
        
        certificate_arn = response['CertificateArn']
        print(f"📋 New certificate requested: {certificate_arn}")
        print(f"⚠️  Don't forget to validate DNS records in ACM console!")
        
        return certificate_arn
        
    except Exception as e:
        print(f"❌ Error managing certificate for {domain}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    domain = sys.argv[1] if len(sys.argv) > 1 else 'ai.sparetools.dev'
    check_and_update_certificate(domain)
