/**
 * PWA Feature Test Script
 * Tests offline storage, sync manager, and PWA manifest
 */

const fs = require('fs');
const path = require('path');

console.log('🧪 Just Travel PWA - Feature Test Suite\n');
console.log('=' .repeat(60));

let passedTests = 0;
let failedTests = 0;

function test(name, fn) {
  try {
    fn();
    console.log(`✅ PASS: ${name}`);
    passedTests++;
  } catch (error) {
    console.log(`❌ FAIL: ${name}`);
    console.log(`   Error: ${error.message}`);
    failedTests++;
  }
}

// Test 1: Manifest exists and is valid JSON
test('Manifest file exists and is valid JSON', () => {
  const manifestPath = path.join(__dirname, 'public', 'manifest.json');
  if (!fs.existsSync(manifestPath)) {
    throw new Error('manifest.json not found');
  }
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  if (!manifest.name || !manifest.short_name || !manifest.icons) {
    throw new Error('Manifest missing required fields');
  }
  if (manifest.icons.length !== 10) {
    throw new Error(`Expected 10 icons, found ${manifest.icons.length}`);
  }
});

// Test 2: All icons exist
test('All 10 icon files exist', () => {
  const iconsDir = path.join(__dirname, 'public', 'icons');
  const requiredIcons = [
    'icon-72x72.png',
    'icon-96x96.png',
    'icon-128x128.png',
    'icon-144x144.png',
    'icon-152x152.png',
    'icon-192x192.png',
    'icon-384x384.png',
    'icon-512x512.png',
    'icon-maskable-192x192.png',
    'icon-maskable-512x512.png'
  ];

  requiredIcons.forEach(icon => {
    const iconPath = path.join(iconsDir, icon);
    if (!fs.existsSync(iconPath)) {
      throw new Error(`Icon ${icon} not found`);
    }
  });
});

// Test 3: Service worker exists
test('Service worker file exists', () => {
  const swPath = path.join(__dirname, 'public', 'sw.js');
  if (!fs.existsSync(swPath)) {
    throw new Error('sw.js not found');
  }
  const swContent = fs.readFileSync(swPath, 'utf8');
  if (swContent.length < 100) {
    throw new Error('Service worker file too small, likely empty');
  }
});

// Test 4: Workbox runtime exists
test('Workbox runtime file exists', () => {
  const publicDir = path.join(__dirname, 'public');
  const files = fs.readdirSync(publicDir);
  const workboxFile = files.find(f => f.startsWith('workbox-') && f.endsWith('.js'));
  if (!workboxFile) {
    throw new Error('Workbox runtime file not found');
  }
});

// Test 5: Offline storage module exists
test('Offline storage module exists', () => {
  const offlinePath = path.join(__dirname, 'lib', 'offline-storage.ts');
  if (!fs.existsSync(offlinePath)) {
    throw new Error('offline-storage.ts not found');
  }
  const content = fs.readFileSync(offlinePath, 'utf8');
  if (!content.includes('class OfflineStorage')) {
    throw new Error('OfflineStorage class not found');
  }
  if (!content.includes('IndexedDB')) {
    throw new Error('IndexedDB implementation not found');
  }
});

// Test 6: Sync manager module exists
test('Sync manager module exists', () => {
  const syncPath = path.join(__dirname, 'lib', 'sync-manager.ts');
  if (!fs.existsSync(syncPath)) {
    throw new Error('sync-manager.ts not found');
  }
  const content = fs.readFileSync(syncPath, 'utf8');
  if (!content.includes('class SyncManager')) {
    throw new Error('SyncManager class not found');
  }
  if (!content.includes('localStorage')) {
    throw new Error('localStorage implementation not found');
  }
});

// Test 7: Online status hook exists
test('Online status hook exists', () => {
  const hookPath = path.join(__dirname, 'hooks', 'useOnlineStatus.ts');
  if (!fs.existsSync(hookPath)) {
    throw new Error('useOnlineStatus.ts not found');
  }
  const content = fs.readFileSync(hookPath, 'utf8');
  if (!content.includes('navigator.onLine')) {
    throw new Error('navigator.onLine not used');
  }
});

// Test 8: Offline banner component exists
test('Offline banner component exists', () => {
  const bannerPath = path.join(__dirname, 'components', 'OfflineBanner.tsx');
  if (!fs.existsSync(bannerPath)) {
    throw new Error('OfflineBanner.tsx not found');
  }
  const content = fs.readFileSync(bannerPath, 'utf8');
  if (!content.includes('useOnlineStatus')) {
    throw new Error('useOnlineStatus hook not imported');
  }
});

// Test 9: Install prompt component exists
test('Install prompt component exists', () => {
  const promptPath = path.join(__dirname, 'components', 'InstallPrompt.tsx');
  if (!fs.existsSync(promptPath)) {
    throw new Error('InstallPrompt.tsx not found');
  }
  const content = fs.readFileSync(promptPath, 'utf8');
  if (!content.includes('beforeinstallprompt')) {
    throw new Error('beforeinstallprompt event not handled');
  }
});

// Test 10: My Itineraries page exists
test('My Itineraries page exists', () => {
  const pagePath = path.join(__dirname, 'app', 'my-itineraries', 'page.tsx');
  if (!fs.existsSync(pagePath)) {
    throw new Error('my-itineraries page not found');
  }
  const content = fs.readFileSync(pagePath, 'utf8');
  if (!content.includes('offlineStorage')) {
    throw new Error('offlineStorage not imported');
  }
  if (!content.includes('getAllItineraries')) {
    throw new Error('getAllItineraries not called');
  }
});

// Test 11: Offline fallback page exists
test('Offline fallback page exists', () => {
  const pagePath = path.join(__dirname, 'app', 'offline', 'page.tsx');
  if (!fs.existsSync(pagePath)) {
    throw new Error('offline page not found');
  }
});

// Test 12: Layout has PWA meta tags
test('Layout has PWA configuration', () => {
  const layoutPath = path.join(__dirname, 'app', 'layout.tsx');
  if (!fs.existsSync(layoutPath)) {
    throw new Error('layout.tsx not found');
  }
  const content = fs.readFileSync(layoutPath, 'utf8');
  if (!content.includes('manifest')) {
    throw new Error('manifest link not found');
  }
  if (!content.includes('OfflineBanner')) {
    throw new Error('OfflineBanner not imported');
  }
  if (!content.includes('InstallPrompt')) {
    throw new Error('InstallPrompt not imported');
  }
});

// Test 13: Main page has offline support
test('Main page has offline support', () => {
  const pagePath = path.join(__dirname, 'app', 'page.tsx');
  if (!fs.existsSync(pagePath)) {
    throw new Error('page.tsx not found');
  }
  const content = fs.readFileSync(pagePath, 'utf8');
  if (!content.includes('useOnlineStatus')) {
    throw new Error('useOnlineStatus hook not imported');
  }
  if (!content.includes('offlineStorage')) {
    throw new Error('offlineStorage not imported');
  }
  if (!content.includes('syncManager')) {
    throw new Error('syncManager not imported');
  }
});

// Test 14: NavHeader has My Trips link
test('NavHeader has My Trips navigation link', () => {
  const navPath = path.join(__dirname, 'components', 'NavHeader.tsx');
  if (!fs.existsSync(navPath)) {
    throw new Error('NavHeader.tsx not found');
  }
  const content = fs.readFileSync(navPath, 'utf8');
  if (!content.includes('/my-itineraries')) {
    throw new Error('My Trips link not found');
  }
});

// Test 15: next.config has PWA wrapper
test('next.config has PWA configuration', () => {
  const configPath = path.join(__dirname, 'next.config.js');
  if (!fs.existsSync(configPath)) {
    throw new Error('next.config.js not found');
  }
  const content = fs.readFileSync(configPath, 'utf8');
  if (!content.includes('withPWA')) {
    throw new Error('withPWA wrapper not found');
  }
  if (!content.includes('runtimeCaching')) {
    throw new Error('runtimeCaching configuration not found');
  }
});

// Summary
console.log('\n' + '='.repeat(60));
console.log(`\n📊 Test Results:`);
console.log(`   Passed: ${passedTests}`);
console.log(`   Failed: ${failedTests}`);
console.log(`   Total:  ${passedTests + failedTests}`);

if (failedTests === 0) {
  console.log(`\n🎉 All tests passed! PWA implementation verified.\n`);
  process.exit(0);
} else {
  console.log(`\n⚠️  ${failedTests} test(s) failed. Please review.\n`);
  process.exit(1);
}
