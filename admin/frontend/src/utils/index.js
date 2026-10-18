export function formatDateTime(timestamp) {
  if (!timestamp) return '-'
  const date = new Date(timestamp)
  const pad = (n) => n.toString().padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

export function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export function formatStatus(status) {
  const statusMap = {
    active: { label: 'Active', type: 'success' },
    offline: { label: 'Offline', type: 'info' },
    pending: { label: 'Pending', type: 'warning' },
    executing: { label: 'Executing', type: 'primary' },
    completed: { label: 'Completed', type: 'success' },
    failed: { label: 'Failed', type: 'danger' },
    'in-transit': { label: 'In Transit', type: 'primary' },
    exfiltrated: { label: 'Exfiltrated', type: 'success' },
    blocked: { label: 'Blocked', type: 'danger' }
  }
  return statusMap[status] || { label: status, type: 'default' }
}

export function getWalletTypeName(walletType) {
  const walletTypes = {
    metamask: 'MetaMask',
    trust: 'Trust Wallet',
    coinbase: 'Coinbase Wallet',
    imtoken: 'imToken',
    tokenpocket: 'TokenPocket',
    alphawallet: 'AlphaWallet',
    mathwallet: 'MathWallet',
    tronlink: 'TronLink',
    onto: 'ONTO',
    bitpie: 'Bitpie',
    huobi: 'Huobi Wallet',
    phantom: 'Phantom',
    keplr: 'Keplr',
    cosmostation: 'Cosmostation'
  }
  return walletTypes[walletType] || walletType
}

export function getCategoryName(category) {
  const categories = {
    'keychain': 'Keychain',
    'wifi': 'WiFi',
    'photos': 'Photos',
    'contacts': 'Contacts',
    'sms': 'SMS',
    'calls': 'Calls',
    'files': 'Files',
    'wallet': 'Wallet',
    'system_info': 'System Info',
    'fingerprint': 'Fingerprint',
    'cookies': 'Cookies',
    'storage': 'Storage',
    'installed_apps': 'Installed Apps',
    'network': 'Network',
    'location': 'Location'
  }
  return categories[category] || category
}

export function getCategoryType(category) {
  const types = {
    'keychain': 'danger',
    'wifi': 'warning',
    'photos': 'success',
    'contacts': 'primary',
    'sms': 'info',
    'calls': 'info',
    'files': 'info',
    'wallet': 'warning',
    'system_info': 'primary',
    'fingerprint': 'success',
    'cookies': 'warning',
    'storage': 'info',
    'installed_apps': 'danger',
    'network': 'success',
    'location': 'danger'
  }
  return types[category] || 'info'
}

export function truncateText(text, maxLength = 50) {
  if (!text) return '-'
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}