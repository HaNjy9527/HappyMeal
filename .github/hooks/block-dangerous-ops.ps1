$structuredRawInput = [Console]::In.ReadToEnd()

function Write-StructuredHookDecision {
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

function Get-StructuredValue {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Object,
        [Parameter(Mandatory = $true)]
        [string[]]$PropertyNames
    )

    foreach ($propertyName in $PropertyNames) {
        if ($null -eq $Object) {
            return $null
        }

        $property = $Object.PSObject.Properties[$propertyName]
        if ($null -ne $property -and $null -ne $property.Value -and $property.Value -ne '') {
            return $property.Value
        }
    }

    return $null
}

function Normalize-StructuredPath {
    param([string]$Path)

    if (-not $Path) {
        return ''
    }

    return $Path.Replace('/', '\').ToLowerInvariant()
}

function Test-StructuredSafePath {
    param([string]$Path)

    $normalizedPath = Normalize-StructuredPath -Path $Path
    if (-not $normalizedPath) {
        return $false
    }

    # 這些資料夾常見於後端日常開發、補測試與暫存清理，預設不直接 deny。
    return (
        $normalizedPath -match '(^|\\)backend\\app(\\|$)' -or
        $normalizedPath -match '(^|\\)backend\\tests(\\|$)' -or
        $normalizedPath -match '(^|\\)backend\\tmp\\analysis-uploads(\\|$)' -or
        $normalizedPath -match '(^|\\)docs(\\|$)'
    )
}

function Test-StructuredSensitivePath {
    param([string]$Path)

    $normalizedPath = Normalize-StructuredPath -Path $Path
    if (-not $normalizedPath) {
        return $false
    }

    $envPattern = '(^|\\)\.' + 'env($|\.|\\)'
    $namePattern = '(^|\\)(' + ((@(
        'se' + 'cret'
        'se' + 'crets'
        'k' + 'ey'
        'k' + 'eys'
        'cre' + 'dential'
        'cre' + 'dentials'
    ) -join '|')) + ')(\\|$)'

    return ($normalizedPath -match $envPattern -or $normalizedPath -match $namePattern)
}

function Get-StructuredDeletedPaths {
    param([string]$PatchText)

    if (-not $PatchText) {
        return @()
    }

    $matches = [regex]::Matches($PatchText, '(?mi)^\*\*\* Delete File: (?<path>.+)$')
    $paths = @()

    foreach ($match in $matches) {
        $paths += $match.Groups['path'].Value.Trim()
    }

    return $paths
}

if (-not $structuredRawInput) {
    Write-StructuredHookDecision -Decision 'allow'
}

try {
    # 只解析當前 tool payload，避免 explanation 與 patch 本文誤觸 regex。
    $structuredPayload = $structuredRawInput | ConvertFrom-Json -Depth 20
}
catch {
    Write-StructuredHookDecision -Decision 'allow'
}

$structuredToolName = [string](Get-StructuredValue -Object $structuredPayload -PropertyNames @('tool_name', 'toolName', 'name', 'recipient_name'))
$structuredToolInput = Get-StructuredValue -Object $structuredPayload -PropertyNames @('input', 'arguments', 'params')

if ($structuredToolName -match '(?i)(^|\.)run_in_terminal$') {
    $structuredCommand = [string](Get-StructuredValue -Object $structuredToolInput -PropertyNames @('command'))

    if (-not $structuredCommand) {
        Write-StructuredHookDecision -Decision 'allow'
    }

    $structuredPatterns = @(
        '(?i)(^|[^A-Za-z])(r' + 'm|d' + 'el|er' + 'ase)\s+'
        '(?i)(^|[^A-Za-z])(rmd' + 'ir|r' + 'd)\s+'
        ('(?i)\b' + ('Remove' + '-Item') + '\b')
        ('(?i)\b' + ('Remove' + '-ItemProperty') + '\b')
        ('(?i)\b' + 'git\s+' + 'reset\s+--hard\b')
        ('(?i)\b' + 'git\s+' + 'clean\s+-[a-z]*f[a-z]*\b')
        ('(?i)\b' + 'docker\s+' + 'system\s+' + 'prune\b')
        ('(?i)\b' + 'docker\s+(' + 'image|container|volume|network)\s+' + 'prune\b')
    )

    foreach ($structuredPattern in $structuredPatterns) {
        if ($structuredCommand -match $structuredPattern) {
            if ($structuredCommand -match '(?i)backend[\\/]app|backend[\\/]tests|backend[\\/]tmp[\\/]analysis-uploads|(^|\s)docs[\\/]') {
                Write-StructuredHookDecision -Decision 'ask' -Reason 'Workspace hook detected a destructive command in a low-risk workspace path. Confirm before proceeding.'
            }

            Write-StructuredHookDecision -Decision 'deny' -Reason 'Workspace hook blocked a dangerous terminal command.'
        }
    }

    Write-StructuredHookDecision -Decision 'allow'
}

if ($structuredToolName -match '(?i)(^|\.)apply_patch$') {
    $structuredPatchText = [string](Get-StructuredValue -Object $structuredToolInput -PropertyNames @('input'))

    foreach ($structuredDeletedPath in (Get-StructuredDeletedPaths -PatchText $structuredPatchText)) {
        if (Test-StructuredSafePath -Path $structuredDeletedPath) {
            continue
        }

        if (Test-StructuredSensitivePath -Path $structuredDeletedPath) {
            Write-StructuredHookDecision -Decision 'deny' -Reason 'Workspace hook blocked deletion of a sensitive file.'
        }

        Write-StructuredHookDecision -Decision 'ask' -Reason 'Workspace hook detected file deletion outside the safe-path allowlist.'
    }

    Write-StructuredHookDecision -Decision 'allow'
}

if ($structuredToolName -match '(?i)(^|\.)(de' + 'lete' + '_file|deletefile|delete)$') {
    $structuredTargetPath = [string](Get-StructuredValue -Object $structuredToolInput -PropertyNames @('filePath', 'path'))

    if (Test-StructuredSensitivePath -Path $structuredTargetPath) {
        Write-StructuredHookDecision -Decision 'deny' -Reason 'Workspace hook blocked deletion of a sensitive file.'
    }

    if (Test-StructuredSafePath -Path $structuredTargetPath) {
        Write-StructuredHookDecision -Decision 'ask' -Reason 'Workspace hook detected deletion in a low-risk path. Confirm before proceeding.'
    }

    Write-StructuredHookDecision -Decision 'ask' -Reason 'Workspace hook requires confirmation for direct file deletion tools.'
}

Write-StructuredHookDecision -Decision 'allow'