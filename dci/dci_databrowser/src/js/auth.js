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

require('./app.js')

.constant('authStates', {
  'DISCONNECTED': 0,
  'AUTHENTICATING': 1,
  'AUTHENTICATED': 2
})

.config(['$httpProvider', function ($httpProvider) {
  $httpProvider.interceptors.push([
    '$q', 'authStates', 'auth', function($q, authStates, auth) {
      return {
        request: function (config) {
          if (auth.state === authStates.DISCONNECTED) {
            config.status = 401;
          } else {
            config.headers.Authorization = 'Basic ' + auth.token;
          }
          return config
        },
        responseError: function (error) {
          if (error.status === 401) {
            auth.state = authStates.DISCONNECTED;
          }
          return $q.reject(error);
        }
      }
    }]);
}])

.service('auth', [
  '$window', '$cookies', 'authStates',
  function ($window, $cookies, authStates) {
    this.token = $cookies.token;
    this.state = angular.isDefined(this.token)
    && authStates.AUTHENTICATED
      || authStates.DISCONNECTED;

      this.login = function(username, password) {
        this.token = $cookies.token =
          $window.btoa(username.concat(':', password));

          this.state = authStates.AUTHENTICATED;
      }

      this.isAuthenticated = function() {
        return this.state === authStates.AUTHENTICATED;
      }

      this.logout = function() {
        $cookies.auth = $window.btoa('None');
        this.state = authStates.DISCONNECTED
      }

  }
])
