#!/usr/bin/env node

/**
 * Deployment Verification Script
 *
 * Usage:
 *   node verify-deployment.js <railway-url> <vercel-url>
 *
 * Example:
 *   node verify-deployment.js https://your-app.railway.app https://your-app.vercel.app
 */

const https = require('https');
const http = require('http');

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function makeRequest(url, method = 'GET') {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const lib = urlObj.protocol === 'https:' ? https : http;

    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port,
      path: urlObj.pathname + urlObj.search,
      method: method,
      headers: {
        'User-Agent': 'Deployment-Verification-Script'
      },
      timeout: 10000
    };

    const req = lib.request(options, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          body: data
        });
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });

    req.end();
  });
}

async function checkBackendHealth(railwayUrl) {
  log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'cyan');
  log('   BACKEND HEALTH CHECK (Railway)', 'cyan');
  log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'cyan');

  try {
    log(`\n→ Testing: ${railwayUrl}/health`, 'blue');
    const response = await makeRequest(`${railwayUrl}/health`);

    if (response.statusCode === 200) {
      log('✓ Backend health check passed', 'green');
      log(`  Status: ${response.statusCode}`, 'green');
      try {
        const data = JSON.parse(response.body);
        log(`  Response: ${JSON.stringify(data)}`, 'green');
      } catch (e) {
        log(`  Response: ${response.body}`, 'green');
      }
      return true;
    } else {
      log(`✗ Backend health check failed`, 'red');
      log(`  Status: ${response.statusCode}`, 'red');
      return false;
    }
  } catch (error) {
    log(`✗ Backend health check failed: ${error.message}`, 'red');
    return false;
  }
}

async function checkBackendStatus(railwayUrl) {
  log('\n→ Testing: /api/status', 'blue');

  try {
    const response = await makeRequest(`${railwayUrl}/api/status`);

    if (response.statusCode === 200) {
      log('✓ Status endpoint accessible', 'green');
      try {
        const data = JSON.parse(response.body);
        log(`  WhatsApp Connected: ${data.connected ? 'Yes' : 'No'}`, data.connected ? 'green' : 'yellow');
        log(`  WhatsApp Ready: ${data.ready ? 'Yes' : 'No'}`, data.ready ? 'green' : 'yellow');
      } catch (e) {
        log(`  Response: ${response.body}`, 'green');
      }
      return true;
    } else {
      log(`✗ Status endpoint failed: ${response.statusCode}`, 'red');
      return false;
    }
  } catch (error) {
    log(`✗ Status endpoint error: ${error.message}`, 'red');
    return false;
  }
}

async function checkFrontend(vercelUrl) {
  log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'cyan');
  log('   FRONTEND CHECK (Vercel)', 'cyan');
  log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'cyan');

  try {
    log(`\n→ Testing: ${vercelUrl}`, 'blue');
    const response = await makeRequest(vercelUrl);

    if (response.statusCode === 200) {
      log('✓ Frontend is accessible', 'green');
      log(`  Status: ${response.statusCode}`, 'green');

      // Check if it's a React app
      if (response.body.includes('id="root"') || response.body.includes('div id="app"')) {
        log('  React app detected', 'green');
      }

      return true;
    } else if (response.statusCode >= 300 && response.statusCode < 400) {
      log(`→ Redirect detected (${response.statusCode})`, 'yellow');
      log(`  Location: ${response.headers.location}`, 'yellow');
      return true;
    } else {
      log(`✗ Frontend check failed: ${response.statusCode}`, 'red');
      return false;
    }
  } catch (error) {
    log(`✗ Frontend error: ${error.message}`, 'red');
    return false;
  }
}

async function checkCORS(railwayUrl, vercelUrl) {
  log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'cyan');
  log('   CORS CONFIGURATION CHECK', 'cyan');
  log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'cyan');

  try {
    log(`\n→ Testing CORS from frontend to backend`, 'blue');
    const response = await makeRequest(`${railwayUrl}/health`);

    const corsHeaders = response.headers['access-control-allow-origin'];
    if (corsHeaders) {
      log('✓ CORS headers present', 'green');
      log(`  Access-Control-Allow-Origin: ${corsHeaders}`, 'green');

      if (corsHeaders === '*' || corsHeaders === vercelUrl) {
        log('  CORS is correctly configured', 'green');
        return true;
      } else {
        log(`  Warning: CORS may not allow ${vercelUrl}`, 'yellow');
        return true;
      }
    } else {
      log('→ CORS headers not found (may need to add)', 'yellow');
      return true;
    }
  } catch (error) {
    log(`✗ CORS check error: ${error.message}`, 'red');
    return false;
  }
}

async function checkEnvironmentVariables(railwayUrl) {
  log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'cyan');
  log('   ENVIRONMENT CHECK', 'cyan');
  log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'cyan');

  log('\n→ Required Railway Environment Variables:', 'blue');
  const requiredEnvVars = [
    'OPENAI_API_KEY or GEMINI_API_KEY',
    'BOSS_PHONE_NUMBER',
    'AUTHORIZATION_PASSWORD',
    'PORT'
  ];

  requiredEnvVars.forEach(envVar => {
    log(`  • ${envVar}`, 'yellow');
  });

  log('\n→ Required Vercel Environment Variables:', 'blue');
  log(`  • VITE_API_URL = ${railwayUrl}`, 'yellow');
  log(`  • VITE_WS_URL = ${railwayUrl.replace('https://', 'wss://')}`, 'yellow');

  log('\nℹ  Please verify these are set in your Railway and Vercel dashboards', 'cyan');
}

async function printSummary(results) {
  log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'cyan');
  log('   DEPLOYMENT SUMMARY', 'cyan');
  log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'cyan');

  const allPassed = results.every(r => r.passed);

  log('\nTest Results:', 'blue');
  results.forEach(result => {
    const icon = result.passed ? '✓' : '✗';
    const color = result.passed ? 'green' : 'red';
    log(`  ${icon} ${result.name}`, color);
  });

  if (allPassed) {
    log('\n🎉 All checks passed! Your deployment is ready.', 'green');
    log('\nNext Steps:', 'cyan');
    log('  1. Open your Vercel URL in a browser', 'blue');
    log('  2. Scan the WhatsApp QR code with your phone', 'blue');
    log('  3. Test sending a message to your WhatsApp number', 'blue');
  } else {
    log('\n⚠  Some checks failed. Please review the errors above.', 'yellow');
    log('\nTroubleshooting:', 'cyan');
    log('  • Check Railway logs: railway logs', 'blue');
    log('  • Check Vercel logs: vercel logs', 'blue');
    log('  • Verify environment variables are set correctly', 'blue');
  }

  log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n', 'cyan');
}

async function main() {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    log('Usage: node verify-deployment.js <railway-url> <vercel-url>', 'red');
    log('\nExample:', 'yellow');
    log('  node verify-deployment.js https://your-app.railway.app https://your-app.vercel.app', 'cyan');
    process.exit(1);
  }

  const railwayUrl = args[0].replace(/\/$/, ''); // Remove trailing slash
  const vercelUrl = args[1].replace(/\/$/, '');

  log('\n╔════════════════════════════════════════════════════════════╗', 'cyan');
  log('║      WhatsApp Secretary AI - Deployment Verification      ║', 'cyan');
  log('╚════════════════════════════════════════════════════════════╝', 'cyan');

  log(`\nRailway URL: ${railwayUrl}`, 'blue');
  log(`Vercel URL:  ${vercelUrl}`, 'blue');

  const results = [];

  // Run all checks
  results.push({
    name: 'Backend Health',
    passed: await checkBackendHealth(railwayUrl)
  });

  results.push({
    name: 'Backend Status API',
    passed: await checkBackendStatus(railwayUrl)
  });

  results.push({
    name: 'Frontend Accessibility',
    passed: await checkFrontend(vercelUrl)
  });

  results.push({
    name: 'CORS Configuration',
    passed: await checkCORS(railwayUrl, vercelUrl)
  });

  await checkEnvironmentVariables(railwayUrl);

  await printSummary(results);
}

main().catch(error => {
  log(`\n✗ Unexpected error: ${error.message}`, 'red');
  console.error(error);
  process.exit(1);
});
