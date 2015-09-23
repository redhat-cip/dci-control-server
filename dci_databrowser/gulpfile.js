'use strict';

var gulp = require('gulp');
var jscs = require('gulp-jscs');

gulp.task('jscs', function() {
    return gulp.src(['src/**.js', 'gulpfile.js'])
           .pipe(jscs());
});

gulp.task('build', function() {
    return gulp.src('src/**').pipe(gulp.dest('static'));
});

gulp.task('test', ['jscs']);
