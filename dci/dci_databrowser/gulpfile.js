'use strict';

var gulp       = require('gulp');
var $          = require('gulp-load-plugins')();
var del        = require('del');
var browserify = require('browserify');
var source     = require('vinyl-source-stream');
var buffer     = require('vinyl-buffer');
var globby     = require('globby');
var through    = require('through2');
var merge      = require('merge2');
var config     = require('./config');
var utils      = require('./utils');

var DIST = 'static';

gulp.task('jscs', function() {
  return gulp.src(['src/**.js', 'gulpfile.js', 'utils.js'])
  .pipe($.jscs());
});

gulp.task('build', ['js', 'css', 'fonts'], function() {
  return gulp.src([
    'src/**/*',
    '!src/**/*.js',
    '!src/**/*.scss'
  ]).pipe(gulp.dest(DIST));
});

gulp.task('clean', function() {
  var entries = [DIST + '/**/*', '!' + DIST + '/.gitkeep'];
  return del(entries);
});

gulp.task('reload', ['build'], function() {
  return $.livereload.reload();
});

gulp.task('watch', function() {
  gulp.watch('src/**', ['reload']);
});

gulp.task('js', ['clean'], function() {
  var bundledStream = through();
  var entries = [
    'node_modules/angular/angular.js',
    'node_modules/angular-cookies/angular-cookies.js',
    'node_modules/angular-resource/angular-resource.js',
    'node_modules/angular-google-chart/ng-google-chart.js',
    'node_modules/angular-bootstrap/ui-bootstrap-tpls.js',
    'node_modules/angular-ui-router/release/angular-ui-router.js',
    'node_modules/angular-loading-bar/build/loading-bar.js',
    'node_modules/moment/moment.js',
    'src/js/**/*.js',
  ];

  globby(entries).then(function(entries) {
    browserify({
      entries: entries,
      debug: true
    }).bundle().pipe(bundledStream);
  }).catch(function(err) {
    // ensure any errors from globby are handled
    bundledStream.emit('error', err);
  });

  return bundledStream
  .pipe(source('app.js'))
  .pipe(buffer())
  .pipe($.sourcemaps.init({loadMaps: true}))
  .pipe($.sourcemaps.write('./'))
  .pipe(gulp.dest(DIST + '/js/'));
});

gulp.task('css', ['clean'], function() {
  var cssEntries = [
    'node_modules/bootstrap/dist/css/bootstrap.css',
    'node_modules/angular-loading-bar/build/loading-bar.css',
    'src/css/**/*.css'
  ];

  var scssEntries = [
    'src/css/**/*.scss'
  ];

  var cssStream = gulp.src(cssEntries);
  var scssStream = gulp.src(scssEntries)
  .pipe($.sass().on('error', $.sass.logError));

  return merge(cssStream, scssStream)
  .pipe($.sourcemaps.init({loadMaps: true}))
  .pipe($.concat('dashboard.css'))
  .pipe($.sourcemaps.write('./'))
  .pipe(gulp.dest(DIST + '/css/'));
});

gulp.task('fonts', ['clean'], function() {
  var entries = [
    'node_modules/bootstrap/dist/fonts/**'
  ];

  return gulp.src(entries)
  .pipe(gulp.dest(DIST + '/fonts/'));
});

gulp.task('serve', ['build'], function() {
  return utils.server(DIST, config.port);
});

gulp.task('serve:dev', ['build', 'watch'], function () {
  return utils.server(DIST, config.port, true);
});

gulp.task('test:e2e', function(cb) {
  var Q = require('q');
  var d = Q.defer();
  var phantom;
  var server;
  var error;

  Q.all([
    utils.server(DIST, config.portTest, false),
    utils.phantom()
  ])
  .then(function(results) {
    phantom = results.pop();
    server = results.pop();
    return utils.protractor(server.address, 'protractor.conf.js');
  })
  .fail(function(err) {
    error = err;
  })
  .fin(function() {
    return Q.all([
      phantom.close(),
      server.close()
    ]);
  })
  .then(function() {
    cb(error);
  });
});

gulp.task('test', ['jscs', 'test:e2e']);
