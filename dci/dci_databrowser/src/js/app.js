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

var moment = require('moment');
var angular = require('angular');
var lodash = require('lodash');

require('angular-cookies');
require('angular-resource');
require('angular-loading-bar');
require('angular-ui-router');
require('angular-google-chart');

module.exports = angular.module('app', [
  'ngCookies', 'angular-loading-bar', 'ui.router', 'googlechart', 'ngResource'
])
.factory('moment', ['_', function(_) {
  moment.locale('en', {invalidDate: 'N/A'});
  moment.locale('fr', {invalidDate: 'N/A'});

  return _.partialRight(moment, moment.ISO_8601, true);
}])
.factory('_', function() {
  return lodash;
})
.factory('glyphiconStatus', ['glyphicons', '_', function(glyphicons, _) {
  return _.partial(_.get, glyphicons);
}])
.constant('glyphicons', {
  'failure': 'glyphicon-remove',
  'success': 'glyphicon-ok',
  'ongoing': 'glyphicon-play',
  'new': 'glyphicon-record',
  'initializing': 'glyphicon-record',
  'killed': 'glyphicon-minus',
  'unfinished': 'glyphicon-minus'
});
