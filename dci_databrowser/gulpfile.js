'use strict';

var gulp = require('gulp');
var connect = require('gulp-connect');
var jscs = require('gulp-jscs');
var config = require('./config');

gulp.task('jscs', function() {
    return gulp.src(['src/**.js', 'gulpfile.js'])
           .pipe(jscs());
});

gulp.task('build', function() {
    return gulp.src('src/**').pipe(gulp.dest('static'));
});

gulp.task('reload', ['build'], function() {
    return gulp.src('static/**').pipe(connect.reload());
});

gulp.task('watch', function() {
    gulp.watch('src/**', ['reload']);
});

gulp.task('connect', function() {
    var url = require('url');
    var proxy = require('proxy-middleware');

    return connect.server({
        host: config.host,
        port: config.port,
        livereload: true,
        root: 'static',
        middleware: function (connect, opt) {
            var options = url.parse(config.api);
            options.route = '/api'

            return [proxy(options)]
        }
    });
});

gulp.task('serve', ['build', 'watch', 'connect'])

gulp.task('test', ['jscs']);
