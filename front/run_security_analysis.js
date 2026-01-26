#!/usr/bin/env node
/**
 * Login Seguro - Script de Análisis de Seguridad Frontend
 * Ejecuta ESLint con reglas de seguridad para detectar vulnerabilidades en TypeScript/React
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('='.repeat(60));
console.log('🔒 LOGIN SEGURO - Análisis de Seguridad Frontend');
console.log('='.repeat(60));
console.log(`📅 Fecha: ${new Date().toISOString()}`);
console.log();

const srcDir = path.join(__dirname, 'src');

if (!fs.existsSync(srcDir)) {
    console.error('❌ Error: Directorio "src" no encontrado');
    process.exit(1);
}

console.log(`📁 Analizando: ${srcDir}`);
console.log();

// Definir patrones de seguridad a buscar
const securityPatterns = [
    { pattern: /dangerouslySetInnerHTML/g, severity: 'HIGH', name: 'XSS Risk: dangerouslySetInnerHTML' },
    { pattern: /eval\s*\(/g, severity: 'HIGH', name: 'Code Injection: eval()' },
    { pattern: /innerHTML\s*=/g, severity: 'HIGH', name: 'XSS Risk: innerHTML assignment' },
    { pattern: /document\.write/g, severity: 'HIGH', name: 'XSS Risk: document.write' },
    { pattern: /localStorage\.setItem.*password/gi, severity: 'HIGH', name: 'Sensitive Data: password in localStorage' },
    { pattern: /localStorage\.setItem.*token/gi, severity: 'MEDIUM', name: 'Token Storage: Consider httpOnly cookies' },
    { pattern: /console\.(log|error|warn)\s*\(/g, severity: 'LOW', name: 'Debug: Console statements' },
    { pattern: /http:\/\//g, severity: 'MEDIUM', name: 'Insecure Protocol: HTTP used' },
    { pattern: /password\s*[:=]\s*['"][^'"]+['"]/g, severity: 'HIGH', name: 'Hardcoded Password' },
    { pattern: /api[_-]?key\s*[:=]\s*['"][^'"]+['"]/gi, severity: 'HIGH', name: 'Hardcoded API Key' },
];

function analyzeFile(filePath) {
    const issues = [];
    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.split('\n');

    securityPatterns.forEach(({ pattern, severity, name }) => {
        pattern.lastIndex = 0; // Reset regex
        let match;
        const contentCopy = content;
        while ((match = pattern.exec(contentCopy)) !== null) {
            // Find line number
            const beforeMatch = contentCopy.substring(0, match.index);
            const lineNumber = (beforeMatch.match(/\n/g) || []).length + 1;
            issues.push({
                file: filePath,
                line: lineNumber,
                severity,
                issue: name,
                match: match[0]
            });
        }
    });

    return issues;
}

function walkDir(dir, fileList = []) {
    const files = fs.readdirSync(dir);
    files.forEach(file => {
        const filePath = path.join(dir, file);
        const stat = fs.statSync(filePath);
        if (stat.isDirectory() && !file.includes('node_modules') && !file.startsWith('.')) {
            walkDir(filePath, fileList);
        } else if (/\.(tsx?|jsx?)$/.test(file)) {
            fileList.push(filePath);
        }
    });
    return fileList;
}

// Analizar archivos
const files = walkDir(srcDir);
console.log(`📄 Archivos a analizar: ${files.length}`);
console.log();

let allIssues = [];
files.forEach(file => {
    const issues = analyzeFile(file);
    allIssues = allIssues.concat(issues);
});

// Contar por severidad
const highIssues = allIssues.filter(i => i.severity === 'HIGH').length;
const mediumIssues = allIssues.filter(i => i.severity === 'MEDIUM').length;
const lowIssues = allIssues.filter(i => i.severity === 'LOW').length;

console.log('📊 RESULTADOS DEL ANÁLISIS');
console.log('-'.repeat(40));
console.log(`   🔴 Alta severidad:   ${highIssues}`);
console.log(`   🟠 Media severidad:  ${mediumIssues}`);
console.log(`   🟡 Baja severidad:   ${lowIssues}`);
console.log(`   📝 Total issues:     ${allIssues.length}`);
console.log();

// Mostrar issues de alta severidad
if (highIssues > 0) {
    console.log('⚠️  ISSUES DE ALTA SEVERIDAD:');
    console.log('-'.repeat(40));
    allIssues.filter(i => i.severity === 'HIGH').forEach(issue => {
        const relativePath = path.relative(__dirname, issue.file);
        console.log(`   📍 ${relativePath}:${issue.line}`);
        console.log(`      ${issue.issue}`);
        console.log(`      Código: ${issue.match}`);
        console.log();
    });
}

// Guardar reporte JSON
const report = {
    timestamp: new Date().toISOString(),
    summary: {
        total: allIssues.length,
        high: highIssues,
        medium: mediumIssues,
        low: lowIssues
    },
    issues: allIssues.map(i => ({
        ...i,
        file: path.relative(__dirname, i.file)
    }))
};

const reportPath = path.join(__dirname, 'security_report_frontend.json');
fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
console.log(`💾 Reporte guardado en: ${reportPath}`);

// También ejecutar ESLint estándar
console.log();
console.log('🔍 Ejecutando ESLint estándar...');
try {
    execSync('npm run lint', { stdio: 'inherit', cwd: __dirname });
    console.log('✅ ESLint completado sin errores');
} catch (e) {
    console.log('⚠️  ESLint encontró algunos issues (ver arriba)');
}

if (highIssues > 0) {
    console.log('\n🚨 ¡Se encontraron vulnerabilidades críticas!');
    process.exit(1);
} else if (mediumIssues > 0) {
    console.log('\n⚠️  Se encontraron vulnerabilidades de nivel medio');
    process.exit(0);
} else {
    console.log('\n✅ No se detectaron vulnerabilidades críticas');
    process.exit(0);
}
