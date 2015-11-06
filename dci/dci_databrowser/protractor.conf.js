exports.config = {
  framework: 'jasmine2',
  seleniumAddress: 'http://localhost:9515',
  specs: ['test/index.spec.js'],
  capabilities: {
    browserName: 'phantomjs'
  },

  onPrepare: function () {
    var jasmineReporters = require('jasmine-reporters');
    jasmine.getEnv().addReporter(
      new jasmineReporters.JUnitXmlReporter()
    );
  },

  // Options to be passed to Jasmine-node.
  jasmineNodeOpts: {
    showColors: true,
    defaultTimeoutInterval: 30000
  }
}
