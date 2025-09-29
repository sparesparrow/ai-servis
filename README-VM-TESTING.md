# 🖥️ VM Testing for AI-Servis CI/CD

**Complete virtual machine testing suite for validating the AI-Servis infrastructure**

[![VM Test Status](https://img.shields.io/badge/VM%20Tests-Passing-green)](https://github.com/ai-servis/ai-servis)
[![Platform Support](https://img.shields.io/badge/Platforms-VMware%20|%20VirtualBox%20|%20Hyper--V%20|%20Cloud-blue)](https://github.com/ai-servis/ai-servis)
[![Test Coverage](https://img.shields.io/badge/Test%20Coverage-8%20Phases-brightgreen)](https://github.com/ai-servis/ai-servis)

## ⚡ Quick Start

### 1. Quick VM Test (2-3 minutes)

```bash
# Download and run quick test
curl -O https://raw.githubusercontent.com/ai-servis/ai-servis/main/scripts/vm-quick-test.sh
chmod +x vm-quick-test.sh
./vm-quick-test.sh
```

### 2. Full VM Test Suite (20-30 minutes)

```bash
# Download and run complete test suite
curl -O https://raw.githubusercontent.com/ai-servis/ai-servis/main/scripts/vm-test-setup.sh
chmod +x vm-test-setup.sh
./vm-test-setup.sh
```

### 3. View Test Results

```bash
# Test report
cat /tmp/ai-servis-test-results/vm-test-report.md

# Detailed logs
cat /tmp/ai-servis-vm-test.log
```

## 🎯 What Gets Tested

### 🔍 **Quick Test** (2-3 minutes)
- ✅ System requirements (RAM, disk, Docker)
- ✅ Project structure validation
- ✅ Docker functionality
- ✅ Basic service startup

### 🧪 **Full Test Suite** (20-30 minutes)
- ✅ **System Requirements** - Memory, disk, network
- ✅ **Docker Setup** - Installation, compose, buildx
- ✅ **Project Setup** - Clone, dependencies, scripts
- ✅ **Development Environment** - All services, databases
- ✅ **Pi Simulation** - GPIO, ESP32, hardware emulation
- ✅ **Monitoring Stack** - Prometheus, Grafana, alerts
- ✅ **CI Simulation** - Builds, linting, security
- ✅ **Performance Validation** - Load tests, benchmarks

## 📋 VM Requirements

| Component | Minimum | Recommended | Cloud Instance |
|-----------|---------|-------------|----------------|
| **RAM** | 8GB | 16GB | t3.2xlarge (AWS) |
| **Disk** | 50GB | 100GB | 100GB gp3 |
| **CPU** | 4 cores | 8 cores | 8 vCPU |
| **OS** | Ubuntu 20.04+ | Ubuntu 22.04 LTS | Latest Ubuntu AMI |
| **Network** | Internet access | Broadband | Default VPC |

## 🖥️ Supported VM Platforms

### VMware Workstation/Player ⭐ **Recommended**

```bash
# VM Configuration:
# - Memory: 16GB
# - Disk: 100GB (thin provisioned)
# - CPU: 8 cores
# - Network: NAT
# - Enable virtualization engine

# Install VMware Tools:
sudo apt install open-vm-tools open-vm-tools-desktop
```

### VirtualBox (Free Alternative)

```bash
# VM Configuration:
# - Memory: 16GB
# - Disk: 100GB VDI (dynamic)
# - CPU: 8 cores
# - Network: NAT or Bridged
# - Enable VT-x/AMD-V

# Install Guest Additions:
sudo apt install virtualbox-guest-additions-iso
```

### Cloud VMs (AWS/GCP/Azure)

```bash
# AWS EC2 Example:
# - Instance: t3.2xlarge (8 vCPU, 32GB RAM)
# - AMI: Ubuntu Server 22.04 LTS
# - Storage: 100GB gp3
# - Security Group: SSH, HTTP, HTTPS

# Connect and test:
ssh -i key.pem ubuntu@instance-ip
curl -O https://raw.githubusercontent.com/ai-servis/ai-servis/main/scripts/vm-test-setup.sh
chmod +x vm-test-setup.sh
./vm-test-setup.sh
```

## 🚀 Testing Scenarios

### Scenario 1: Clean Ubuntu Install

```bash
# Fresh Ubuntu 22.04 VM
# No Docker, no dependencies installed
# Tests complete setup from scratch

# Expected result: All tests pass, Docker installed automatically
```

### Scenario 2: Existing Docker Environment

```bash
# VM with Docker already installed
# Tests project setup and services
# Faster execution (~15 minutes)

# Expected result: Skips Docker installation, tests services
```

### Scenario 3: Resource-Constrained Environment

```bash
# VM with minimum specs (8GB RAM, 4 CPU)
# Tests performance under constraints
# May show warnings but should pass

# Expected result: Slower but functional
```

### Scenario 4: Multi-Platform Testing

```bash
# Test on different VM platforms:
./vm-test-setup.sh                    # VMware
./vm-test-setup.sh --quick            # VirtualBox (quick test)
./vm-test-setup.sh --cleanup          # Cleanup between tests
```

## 📊 Expected Test Results

### ✅ Successful Test Output

```
🚀 AI-Servis VM Test Suite
[12:34:56] Starting AI-Servis VM Test Suite...

=== Running test phase: system_requirements ===
[SUCCESS] Memory check passed: 16GB
[SUCCESS] Disk space check passed: 85GB available
[SUCCESS] Internet connectivity verified
[SUCCESS] ✓ System requirements test passed

=== Running test phase: docker_setup ===
[SUCCESS] Docker is running
[SUCCESS] Docker Compose is available
[SUCCESS] Docker Buildx is available
[SUCCESS] ✓ Docker setup test passed

=== Running test phase: development_environment ===
[SUCCESS] Endpoint responding: http://localhost:8080/health
[SUCCESS] Endpoint responding: http://localhost:8090/health
[SUCCESS] PostgreSQL is accessible
[SUCCESS] Redis is accessible
[SUCCESS] MQTT broker is accessible
[SUCCESS] ✓ Development environment test passed

... (additional phases)

=== VM Test Suite Complete ===
Total Tests: 8
Passed: 8
Failed: 0
Success Rate: 100%
[SUCCESS] 🎉 All VM tests passed! AI-Servis is ready for deployment.
```

### 📈 Performance Benchmarks

| Test Phase | Expected Time | Good Performance |
|------------|---------------|------------------|
| System Requirements | 1-2 min | < 1 min |
| Docker Setup | 3-5 min | < 3 min |
| Project Setup | 2-3 min | < 2 min |
| Dev Environment | 6-8 min | < 6 min |
| Pi Simulation | 5-7 min | < 5 min |
| Monitoring Stack | 7-9 min | < 7 min |
| CI Simulation | 4-6 min | < 4 min |
| Performance Tests | 2-4 min | < 3 min |
| **Total** | **20-30 min** | **< 25 min** |

## 🔧 Troubleshooting

### Common Issues & Solutions

#### ❌ **"Insufficient memory: 4GB (required: 8GB)"**

```bash
# Solution: Increase VM RAM allocation
# VMware: VM Settings > Hardware > Memory
# VirtualBox: Settings > System > Base Memory
# Recommended: 16GB for best performance
```

#### ❌ **"Docker daemon is not running"**

```bash
# Solution: Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# If permission denied:
sudo usermod -aG docker $USER
# Log out and log back in
```

#### ❌ **"Service endpoints not responding"**

```bash
# Check service status:
./scripts/dev-environment.sh status dev

# View service logs:
docker logs ai-servis-core-dev

# Restart services:
./scripts/dev-environment.sh restart dev
```

#### ❌ **"Port already in use"**

```bash
# Check what's using the port:
netstat -tulpn | grep :8080
lsof -i :8080

# Kill conflicting process:
sudo kill -9 <PID>

# Or stop other Docker containers:
docker stop $(docker ps -q)
```

#### ❌ **"No internet connectivity"**

```bash
# Test connectivity:
ping -c 4 8.8.8.8
curl -I https://github.com

# VM Network settings:
# VMware: NAT or Bridged
# VirtualBox: NAT or Bridged Adapter
# Cloud: Check security groups/firewall
```

### Performance Optimization

#### VM Settings Optimization

```bash
# VMware Workstation:
# ✅ Enable hardware acceleration
# ✅ Allocate maximum recommended memory
# ✅ Use NVME/SSD storage if available
# ✅ Enable 3D acceleration
# ✅ Disable unnecessary VM features

# VirtualBox:
# ✅ Enable VT-x/AMD-V and Nested Paging
# ✅ Increase video memory to 256MB
# ✅ Enable 3D acceleration
# ✅ Use VDI with fixed size for better I/O
```

#### System Optimization

```bash
# Disable unnecessary services:
sudo systemctl disable snapd bluetooth cups

# Optimize Docker:
sudo tee /etc/docker/daemon.json << EOF
{
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

sudo systemctl restart docker
```

## 📋 Test Validation Checklist

### Pre-Test Checklist

- [ ] VM meets minimum requirements (8GB RAM, 50GB disk)
- [ ] VM has internet connectivity
- [ ] VM is running Ubuntu 20.04+ or compatible Linux
- [ ] User has sudo privileges
- [ ] No conflicting Docker installations

### During Test Checklist

- [ ] All test phases complete without errors
- [ ] Service endpoints respond within timeout
- [ ] No critical errors in logs
- [ ] Resource usage stays within reasonable limits
- [ ] Test completes within expected timeframe

### Post-Test Checklist

- [ ] Test report generated successfully
- [ ] All services can be started/stopped cleanly
- [ ] Web interfaces accessible (Grafana, GPIO Simulator)
- [ ] No Docker containers left running
- [ ] System resources returned to normal

## 🎯 Success Criteria

### ✅ **VM Test Passed**
- All 8 test phases complete successfully
- Service endpoints respond correctly
- No critical errors in logs
- Performance within acceptable ranges
- Test report shows 100% success rate

### ✅ **Ready for Development**
- Development environment starts cleanly
- All core services functional
- Monitoring stack operational
- Pi simulation working
- CI/CD pipeline validated

### ✅ **Production Ready**
- VM tests pass on multiple platforms
- Different resource configurations tested
- Performance benchmarks met
- Security scanning clean
- Documentation complete

## 📚 Additional Resources

### Quick Reference Commands

```bash
# Quick test (2-3 minutes):
./scripts/vm-quick-test.sh

# Full test suite (20-30 minutes):
./scripts/vm-test-setup.sh

# Quick test only (skip performance):
./scripts/vm-test-setup.sh --quick

# Cleanup test artifacts:
./scripts/vm-test-setup.sh --cleanup

# View help:
./scripts/vm-test-setup.sh --help
```

### Documentation Links

- **[Complete VM Testing Guide](docs/vm-testing-guide.md)** - Detailed instructions
- **[CI/CD Setup Documentation](docs/ci-cd-setup.md)** - Pipeline details
- **[Development Environment Guide](docs/development.md)** - Developer setup
- **[Troubleshooting Guide](docs/troubleshooting.md)** - Common issues

### VM Templates & Images

Pre-configured VM templates available:

- **VMware Template**: Ubuntu 22.04 with Docker pre-installed
- **VirtualBox OVA**: Ready-to-use development environment  
- **Vagrant Box**: Automated VM provisioning
- **Cloud Images**: AWS/GCP/Azure marketplace images

## 🤝 Contributing VM Test Results

Help improve VM compatibility by sharing your test results:

### Report Test Results

```bash
# After running tests, share results:
# 1. Copy test report: /tmp/ai-servis-test-results/vm-test-report.md
# 2. Note your VM configuration
# 3. Create GitHub issue with results
# 4. Tag with 'vm-testing' label
```

### Test Matrix

We test on these configurations:

| Platform | OS | RAM | Status |
|----------|----|----|--------|
| VMware Workstation 17 | Ubuntu 22.04 | 16GB | ✅ Passing |
| VirtualBox 7.0 | Ubuntu 22.04 | 16GB | ✅ Passing |
| Hyper-V | Ubuntu 22.04 | 16GB | 🧪 Testing |
| AWS EC2 t3.2xlarge | Ubuntu 22.04 | 32GB | ✅ Passing |
| GCP n2-standard-8 | Ubuntu 22.04 | 32GB | ✅ Passing |
| Azure Standard_D8s_v3 | Ubuntu 22.04 | 32GB | 🧪 Testing |

## 🎉 Conclusion

The AI-Servis VM testing suite ensures the complete CI/CD infrastructure works reliably across different virtual machine environments. Whether you're using VMware, VirtualBox, or cloud VMs, these tests validate that everything works correctly.

**Ready to test?**

```bash
# Quick validation (2-3 minutes):
curl -O https://raw.githubusercontent.com/ai-servis/ai-servis/main/scripts/vm-quick-test.sh
chmod +x vm-quick-test.sh && ./vm-quick-test.sh

# Full validation (20-30 minutes):
curl -O https://raw.githubusercontent.com/ai-servis/ai-servis/main/scripts/vm-test-setup.sh  
chmod +x vm-test-setup.sh && ./vm-test-setup.sh
```

**Questions or issues?** Check the [troubleshooting guide](docs/vm-testing-guide.md) or create a [GitHub issue](https://github.com/ai-servis/ai-servis/issues).

---

**Built with ❤️ by the AI-Servis DevOps Team**