exports.config = {
  execArgv: ['--inspect'],
  specs: [
    './tests/**/*.js'
  ],
  exclude: [
    // 'path/to/excluded/files'
  ],
  // Capabilities
  maxInstances: 2,
  capabilities: [
    {
      browserName: 'firefox',
      maxInstances: 1,
      //args: '[--jsdebugger]',
      'moz:firefoxOptions': {
      // []
      }
    }
  ],
  sync: true,
  logLevel: 'verbose',
  logOutput: './log',
  coloredLogs: true,
  deprecationWarnings: true,
  bail: 0,
  screenshotPath: './errorShots',
  baseUrl: 'http://localhost',
  waitforTimeout: 10000,
  connectionRetryTimeout: 90000,
  connectionRetryCount: 3,
  services: [],
  seleniumLogs: './log',
  framework: 'mocha',
  reporters: ['spec'],
  mochaOpts: {
    es_staging: 1,
    ui: 'bdd',
    require: 'babel-register',
    retries: 3
  }
}
