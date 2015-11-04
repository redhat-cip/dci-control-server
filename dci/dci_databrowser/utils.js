'use strict';

var config       = require('./config');
var connect      = require('connect');
var http         = require('http');
var url          = require('url');
var path         = require('path');
var Q            = require('q');
var proxy        = require('proxy-middleware');
var gutil        = require('gulp-util');
var serveStatic  = require('serve-static');
var childProcess = require('child_process');

/*
 * The close function is async, so we wrap it in order
 * to make it return a promise
 */
function closePromise(obj) {
  var oldClose = obj.close;
  obj.close = function() {
    var d = Q.defer();
    obj.on('close', d.resolve);
    oldClose.call(obj);
    return d.promise;
  };
}

function server(root, port, livereload) {
  var d = Q.defer();
  var api = process.env.API_PORT_5000_TCP + '/api' || config.api;
  var app = connect();

  api = url.parse(api);
  // must be present here in the case of using docker compose
  api.protocol = 'http:';
  api.route = '/api';

  if (livereload) {
    var options = {host: config.host, port: 35729};
    require('gulp-livereload').listen(options, function() {
      gutil.log('Livereload started on port:',
                gutil.colors.green(options.port));
    })
    app.use(require('connect-livereload')({port: options.port}));
  }
  app.use(serveStatic(root));
  app.use(proxy(api));

  var server = http.createServer(app);
  closePromise(server);
  server
  .on('listening', function() {
    var connection = server._connectionKey.split(':');
    var address = {
      protocol: 'http',
      hostname: connection[1],
      port: connection[2]
    };
    gutil.log('Server started at:', gutil.colors.green(url.format(address)));
    server.address = address;
    d.resolve(server);
  })
  .on('close', function() {
    gutil.log('Server', gutil.colors.blue('stopped'));
  });

  server.listen(port, config.host);

  return d.promise;
}

function phantom() {
  var d = Q.defer();

  var child = childProcess.execFile(
    require('phantomjs').path, ['--webdriver=9515']
  );

  //convenient alias
  child.close = child.kill;
  closePromise(child);

  child.stdout
  .on('data', function(chunk) {
    if (chunk.indexOf('GhostDriver') > -1 && chunk.indexOf('running') > -1) {
      gutil.log('Phantomjs started');
      d.resolve(child);
    }
  })
  .on('close', function() {
    gutil.log('Phantomjs', gutil.colors.blue('stopped'));
  });

  process.on('SIGINT', child.kill);

  return d.promise;
}

function protractor(address, configFile) {
  var args = ['--baseUrl', url.format(address)];
  var d = Q.defer();

  var child = childProcess
  .fork(path.join(__dirname, 'node_modules/protractor/lib/cli'), args)
  .on('close', function(errorCode) {
    gutil.log('Protractor', gutil.colors.blue('stopped'));
    if (errorCode === 0) {
      d.resolve();
    } else {
      d.reject(new gutil.PluginError(
        'protractor', 'exited with non 0 status code'
      ));
    }
  });

  process.on('SIGINT', child.kill);

  return d.promise;
}

module.exports = {
  server: server,
  phantom: phantom,
  protractor: protractor
};
