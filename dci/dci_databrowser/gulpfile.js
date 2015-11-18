// Copyright 2015 Red Hat, Inc.
//
// Licensed under the Apache License, Version 2.0 (the 'License'); you may
// not use this file except in compliance with the License. You may obtain
// a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an 'AS IS' BASIS, WITHOUT
// WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
// License for the specific language governing permissions and limitations
// under the License.

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
  return gulp.src(['src/**.js', 'test/**.js', 'gulpfile.js', 'utils.js'])
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

  globby(['src/js/**/*.js']).then(function(entries) {
    browserify({
      entries: entries,
      debug: true
    })
    .require('./src/js/app.js', {'expose': 'app'})
    .bundle()
    .pipe(bundledStream);
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

gulp.task('serve:dev', ['build', 'watch'], function() {
  return utils.server(DIST, config.port, true);
});

gulp.task('test:e2e', ['build'], function(cb) {
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
