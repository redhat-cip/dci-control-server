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
