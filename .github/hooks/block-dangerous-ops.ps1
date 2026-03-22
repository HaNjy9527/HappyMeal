$rawInput = [Console]::In.ReadToEnd()

function Write-HookDecision {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('allow', 'ask', 'deny')]
        [string]$Decision,
        [string]$Reason
    )

    $output = @{
        hookSpecificOutput = @{
            hookEventName = 'PreToolUse'
            permissionDecision = $Decision
        }
    }

    if ($Reason) {
        $output.hookSpecificOutput.permissionDecisionReason = $Reason
    }

    $output | ConvertTo-Json -Depth 10 -Compress
    exit 0
}

if (-not $rawInput) {
    Write-HookDecision -Decision 'allow'
}

$deleteToolPattern = '(?i)"tool_(name|Name)"\s*:\s*"(delete_file|deleteFile|Delete)"'
if ($rawInput -match $deleteToolPattern) {
    Write-HookDecision -Decision 'deny' -Reason 'Workspace hook blocked direct file deletion tools.'
}

$blockedPatterns = @(
    '(?i)(^|[^A-Za-z])(rm|del|erase)\s+'
    '(?i)(^|[^A-Za-z])(rmdir|rd)\s+'
    '(?i)\bRemove-Item\b'
    '(?i)\bRemove-ItemProperty\b'
    '(?i)\bgit\s+reset\s+--hard\b'
    '(?i)\bgit\s+clean\s+-[a-z]*f[a-z]*\b'
    '(?i)\bdocker\s+system\s+prune\b'
    '(?i)\bdocker\s+(image|container|volume|network)\s+prune\b'
)

foreach ($pattern in $blockedPatterns) {
    if ($rawInput -match $pattern) {
        Write-HookDecision -Decision 'deny' -Reason 'Workspace hook blocked a dangerous terminal command.'
    }
}

$sensitiveDeletePattern = '(?i)(rm|del|erase|rmdir|rd|Remove-Item).*(\.env|secret|secrets|key|keys|credential|credentials)'
if ($rawInput -match $sensitiveDeletePattern) {
    Write-HookDecision -Decision 'deny' -Reason 'Workspace hook blocked sensitive file deletion.'
}

Write-HookDecision -Decision 'allow'