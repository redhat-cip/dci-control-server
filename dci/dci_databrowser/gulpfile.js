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

var gulp   = require('gulp');
var $      = require('gulp-load-plugins')();
var del    = require('del');
var source = require('vinyl-source-stream');
var buffer = require('vinyl-buffer');
var config = require('./config');
var utils  = require('./utils');

var DIST = 'static';
var JS = ['src/js/**/*.js'];
var SCSS = ['src/css/**/*.scss'];

gulp.task('jscs', function() {
  return gulp.src(['src/**.js', 'test/**.js', 'gulpfile.js', 'utils.js'])
  .pipe($.jscs());
});

gulp.task('copy', ['clean'], function() {
  return gulp.src([
    'src/**/*',
    '!src/**/*.js',
    '!src/**/*.scss'
  ]).pipe(gulp.dest(DIST));
});

gulp.task('build', ['js', 'css', 'fonts', 'copy']);
gulp.task('build:test', ['js:test', 'css', 'fonts', 'copy']);

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

function buildJS(jsFiles) {
  return utils.bundledStream(jsFiles)
  .pipe(source('app.js'))
  .pipe(buffer())
  .pipe($.sourcemaps.init({loadMaps: true}))
  .pipe($.sourcemaps.write('./'))
  .pipe(gulp.dest(DIST + '/js/'));
}

gulp.task('js', ['clean'], function() {
  return buildJS(JS);
});

gulp.task('js:test', ['clean'], function() {
  return buildJS(JS.concat('node_modules/angular-mocks/ngMockE2E.js'));
});

gulp.task('css', ['clean'], function() {
  var conf = {
    includePaths: ['node_modules/bootstrap-sass/assets/stylesheets/']
  };

  return gulp.src(SCSS)
  .pipe($.sass(conf).on('error', $.sass.logError))
  .pipe($.sourcemaps.init({loadMaps: true}))
  .pipe($.concat('dashboard.css'))
  .pipe($.sourcemaps.write('./'))
  .pipe(gulp.dest(DIST + '/css/'));
});

gulp.task('fonts', ['clean'], function() {
  var entries = [
    'node_modules/bootstrap-sass/assets/fonts/**'
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

gulp.task('test:e2e', ['build:test'], function(cb) {
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

gulp.task('test:e2e:debug', ['build:test'], function(cb) {
  var server;
  var error;
  utils.server(DIST, config.portTest, false)
  .then(function(s) {
    server = s;
    return utils.protractor(server.address, 'protractor.conf.debug.js', true);
  })
  .fail(function(err) {
    error = err;
  })
  .fin(function() {
    server.close();
    cb(error);
  });
});

gulp.task('test', ['jscs', 'test:e2e']);
