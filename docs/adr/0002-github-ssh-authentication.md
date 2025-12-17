# ADR 0002: GitHub SSH Authentication Setup

**Status**: Accepted
**Date**: 2025-12-17
**Deciders**: System Architect, DevOps Team
**Technical Story**: Required during PR #24, #25, #26 merge operations

## Context

During the development and merging of Phases 2 and 3, we encountered SSH authentication issues when pushing branches to GitHub. The repository uses SSH protocol (`git@github.com:Post-X-Society/ans-project.git`) which requires proper SSH key setup.

### Problem

Initial git push operations failed with:
```
git@github.com: Permission denied (publickey).
fatal: Could not read from remote repository.
```

This blocked the automated PR creation and merge workflow.

## Decision

We decided to use **dedicated SSH keys for GitHub** with proper SSH agent configuration to enable seamless git operations for automated and manual workflows.

### SSH Key Configuration

#### 1. SSH Key Location
- **Private Key**: `~/.ssh/id_ed25519_github`
- **Public Key**: `~/.ssh/id_ed25519_github.pub`
- **Algorithm**: ED25519 (modern, secure, performant)

#### 2. SSH Config Setup

File: `~/.ssh/config`

```ssh
# GitHub Configuration
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_github
    IdentitiesOnly yes
    AddKeysToAgent yes
    UseKeychain yes
```

**Configuration Explained**:
- `IdentityFile`: Points to the GitHub-specific SSH key
- `IdentitiesOnly yes`: Only use this specific key (prevents trying other keys)
- `AddKeysToAgent yes`: Automatically add key to SSH agent when used
- `UseKeychain yes`: Store passphrase in macOS Keychain (if key is passphrase-protected)

#### 3. SSH Agent Setup

Commands used during PR workflow:
```bash
# Start SSH agent (if not running)
eval "$(ssh-agent -s)"

# Add GitHub SSH key to agent
ssh-add ~/.ssh/id_ed25519_github

# Verify key is added
ssh-add -l

# Test GitHub connection
ssh -T git@github.com
```

Expected output from test:
```
Hi Post-X-Society/ans-project! You've successfully authenticated, but GitHub does not provide shell access.
```

### Repository Remote Configuration

```bash
# SSH URL (preferred)
origin  git@github.com:Post-X-Society/ans-project.git (fetch)
origin  git@github.com:Post-X-Society/ans-project.git (push)

# HTTPS URL (fallback, requires token)
# origin  https://github.com/Post-X-Society/ans-project.git
```

## Rationale

### Why Dedicated GitHub Key?

1. **Security**: Separate key for GitHub allows revocation without affecting other services
2. **Clarity**: Named `id_ed25519_github` makes purpose obvious
3. **Access Control**: Can be shared with CI/CD systems independently

### Why ED25519?

1. **Security**: More secure than RSA with shorter key length
2. **Performance**: Faster generation and verification
3. **Modern Standard**: Recommended by GitHub and security best practices

### Why SSH Over HTTPS?

1. **No Token Management**: No need to store GitHub Personal Access Tokens
2. **Persistent Auth**: Keys remain valid until revoked
3. **Better for Automation**: SSH agent handles authentication seamlessly

## Consequences

### Positive

✅ **Seamless Git Operations**: Push, pull, fetch work without password prompts
✅ **Automation Ready**: CI/CD and agents can use the same key
✅ **Secure**: Private key never leaves the machine, SSH agent handles auth
✅ **Persistent**: No token expiration to manage

### Negative

⚠️ **Initial Setup Required**: Each developer must configure SSH keys
⚠️ **Key Management**: Need to back up private key securely
⚠️ **Agent Dependency**: SSH agent must be running for passphrase-protected keys

### Neutral

ℹ️ **Keychain Integration**: macOS Keychain stores passphrase (convenient but machine-specific)
ℹ️ **Multiple Keys**: Can have separate keys for different GitHub accounts

## Implementation Timeline

- **2025-12-12**: Initial SSH key generated (`id_ed25519_github`)
- **2025-12-17**: SSH config added during PR #24 merge
- **2025-12-17**: Successfully used for PR #24, #25, #26 workflow

## Testing & Verification

### Quick Test
```bash
# Test GitHub SSH connection
ssh -T git@github.com

# Expected output:
# Hi Post-X-Society/ans-project! You've successfully authenticated...
```

### Git Operations Test
```bash
# Clone repository
git clone git@github.com:Post-X-Society/ans-project.git

# Push changes
git push origin feature-branch

# Should complete without password prompt
```

## Related ADRs

- ADR 0001: Docker Development Environment (infrastructure setup)
- Future ADR: CI/CD Pipeline Configuration (will use deploy keys)

## References

- [GitHub SSH Documentation](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
- [SSH Config Best Practices](https://www.ssh.com/academy/ssh/config)
- [ED25519 Key Generation](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)

## Public Key

For reference, the public key that was added to GitHub:

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... [truncated for security]
```

**Note**: The private key (`id_ed25519_github`) is never shared and remains on the local machine only.

## Maintenance

### Regular Tasks
- Review GitHub deploy keys quarterly
- Rotate SSH keys annually
- Monitor SSH agent processes

### Troubleshooting

**Problem**: `Permission denied (publickey)`
**Solution**:
1. Check SSH agent: `ssh-add -l`
2. Add key if missing: `ssh-add ~/.ssh/id_ed25519_github`
3. Test connection: `ssh -T git@github.com`

**Problem**: Wrong key being used
**Solution**:
1. Check SSH config: `cat ~/.ssh/config`
2. Verify `IdentitiesOnly yes` is set
3. Remove other keys from agent: `ssh-add -D` then re-add GitHub key

**Problem**: Passphrase prompt on every use
**Solution**:
1. Add key to agent: `ssh-add ~/.ssh/id_ed25519_github`
2. On macOS, ensure `UseKeychain yes` in SSH config
3. Re-add key: `ssh-add --apple-use-keychain ~/.ssh/id_ed25519_github`

---

**Last Updated**: 2025-12-17
**Status**: ✅ Active and Working
