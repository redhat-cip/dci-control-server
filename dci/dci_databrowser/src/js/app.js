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

require('angular-cookies');
require('angular-resource');
require('angular-loading-bar');
require('angular-ui-router');
require('angular-google-chart');

module.exports = angular.module('app', [
  'ngCookies', 'angular-loading-bar', 'ui.router', 'googlechart', 'ngResource'
])
.factory('moment', ['config', function (config) {
  moment.locale('en', {invalidDate: 'N/A'});
  moment.locale('fr', {invalidDate: 'N/A'});

  return function(string) {
    return moment(string, config.datePattern, true);
  }
}])
.value('config', {
  'datePattern': 'ddd, DD MMM YYYY HH:mm:ss [GMT]'
});
