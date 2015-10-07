require('./app.js')

.controller('LoginCtrl', [
  '$scope', '$state', 'auth', function($scope, $state, auth) {
    $scope.authenticate = function(credentials) {
      auth.login(credentials.username, credentials.password);
      $state.go('index');
    }
  }
])

.controller('ListJobsCtrl', [
  '$state', '$scope', 'jobs', 'page', function($state, $scope, jobs, page) {
    $scope.jobs = jobs._items;
    $scope.page = page = page || 1;

    var total = $scope.total =
      Math.ceil(jobs._meta.total / jobs._meta.max_results);

    var go = function(page) {
      return function () {
        $state.go('jobs', {
          'page': page > total && total || page > 0 && page || 1
        });
      }
    }

    $scope.previous = go(page - 1);
    $scope.next = go(page + 1);
  }
]);
