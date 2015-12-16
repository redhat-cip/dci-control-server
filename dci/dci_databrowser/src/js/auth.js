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

require('app')
.constant('userStatus', {
  'DISCONNECTED': 0,
  'UNAUTHORIZED': 1,
  'AUTHENTICATED': 2
})

.value('user', {})

.config(['$httpProvider', function ($httpProvider) {
  var interceptor = ['$q', 'user', 'userStatus', function($q, user, status) {
    var apiURL = new RegExp('api\/');

    return {
      request: function (conf) {
        if (!conf.url.match(apiURL)) return conf;
        if (!user.token) return angular.extend(conf, {status: 401});

        conf.headers['Authorization'] = 'Basic ' + user.token;
        return conf;
      },
      responseError: function(error) {
        if (user.status !== status.DISCONNECTED && error.status === 401) {
          user.status = status.UNAUTHORIZED;
        }
        return $q.reject(error);
      }
    };
  }];
  $httpProvider.interceptors.push(interceptor);

}])
.service('auth', [
  '$window', '$cookieStore', 'api', 'user', 'userStatus',
  function ($window, $cookies, api, user, status) {
    angular.extend(user, {status: status.DISCONNECTED}, $cookies.get('user'));

    this.user = user;

    this.login = function(username, password) {
      user.token = $window.btoa(username.concat(':', password));

      return api.getUser(username).then(function(userRes) {
        angular.extend(user, userRes, {status: status.AUTHENTICATED});
        $cookies.put('user', user);
        return user;
      });
    }

    this.isAuthenticated = function() {
      return user.status === status.AUTHENTICATED;
    }
    this.isUnauthorized = function() {
      return user.status === status.UNAUTHORIZED;
    }

    this.isAdmin = function() {
      return user.team.name === 'admin';
    }

    this.logout = function() {
      $cookies.put('user', {});
      user.status = status.DISCONNECTED;
    }
  }
])
.run(['auth', angular.noop]);

