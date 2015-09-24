'use strict';

var gulp = require('gulp');
var connect = require('gulp-connect');
var jscs = require('gulp-jscs');
var config = require('./config');
var browserify = require('browserify');
var source = require('vinyl-source-stream');
var buffer = require('vinyl-buffer');
var sourcemaps = require('gulp-sourcemaps');

gulp.task('jscs', function() {
    return gulp.src(['src/**.js', 'gulpfile.js'])
           .pipe(jscs());
});

gulp.task('build', ['js'], function() {
    return gulp.src([
        'src/**/*',
        '!src/**/*.js'
    ]).pipe(gulp.dest('static'));
});

gulp.task('reload', ['build'], function() {
    return gulp.src('static/**').pipe(connect.reload());
});

gulp.task('watch', function() {
    gulp.watch('src/**', ['reload']);
});

gulp.task('js', function() {
    var b = browserify({
        entries: [
            'src/js/app.js',
            'node_modules/angular/angular.js',
            'node_modules/angular-route/angular-route.js',
            'node_modules/angular-cookies/angular-cookies.js',
            'node_modules/angular-resource/angular-resource.js',
            'node_modules/angular-google-chart/ng-google-chart.js',
            'node_modules/angular-bootstrap/ui-bootstrap-tpls.js',
            'node_modules/angular-ui-router/release/angular-ui-router.js',
            'node_modules/angular-loading-bar/build/loading-bar.js',
        ],
        debug: true
    });

    return b.bundle()
      .pipe(source('app.js'))
      .pipe(buffer())
      .pipe(sourcemaps.init({loadMaps: true}))
      .pipe(sourcemaps.write('./'))
      .pipe(gulp.dest('./static/js/'));
});

gulp.task('connect', function() {
    var url = require('url');
    var proxy = require('proxy-middleware');

    return connect.server({
        host: config.host,
        port: config.port,
        livereload: true,
        root: 'static',
        middleware: function(connect, opt) {
            var options = url.parse(config.api);
            options.route = '/api';

            return [proxy(options)];
        }
    });
});

gulp.task('serve', ['build', 'watch', 'connect']);

gulp.task('test', ['jscs']);
