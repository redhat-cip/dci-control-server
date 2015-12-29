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
require('angular-ui-router');
require('angular-bootstrap');

module.exports = angular.module('app', [
  'ngCookies', 'ui.router', 'ui.bootstrap'
])
.factory('moment', ['_', function(_) {
  moment.locale('en', {invalidDate: 'N/A'});
  moment.locale('fr', {invalidDate: 'N/A'});

  return _.assign(
    _.partialRight(moment, moment.ISO_8601, true), {'moment': moment}
  );
}])
.factory('_', function() {
  return lodash;
})
.constant('status', {
  'failure': {
    'color': 'danger',
    'glyphicon': 'glyphicon-remove'
  },
  'success': {
    'color': 'success',
    'glyphicon': 'glyphicon-ok'
  },
  'running': {
    'color': 'warning',
    'glyphicon': 'glyphicon-play'
  },
  'new': {
    'color': 'primary',
    'glyphicon': 'glyphicon-record'
  },
  'pre-run': {
    'color': 'info',
    'glyphicon': 'glyphicon-record'
  },
  'post-run': {
    'color': 'info',
    'glyphicon': 'glyphicon-record'
  }
});
