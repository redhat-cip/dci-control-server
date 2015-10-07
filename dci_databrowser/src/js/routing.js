
require('./app.js')
.config([
  '$stateProvider', '$urlRouterProvider',
  function($stateProvider, $urlRouterProvider) {
    var scrollTop = ['$anchorScroll',
      function ($anchorScroll) {$anchorScroll();}
    ];

    $stateProvider
    .state('auth', {
      'abstract': true,
      resolve: {
        _: ['auth', '$q', function (auth, $q) {
          if (auth.isAuthenticated()) {
            return;
          } else {
            return $q.reject(auth.state);
          }
        }]
      },
      controller: 'authCtrl',
      templateUrl: 'partials/auth.html'
    })
    .state('index', {
      url: '/',
      parent: 'auth',
      onEnter: ['$state', function ($state) {
        $state.go('jobs');
      }]
    })
    .state('jobs', {
      url: '/jobs?page',
      parent: 'auth',
      resolve: {
        page: ['$stateParams', function ($stateParams) {
          return parseInt($stateParams.page) || 1;
        }],
        jobs: ['api', 'page', function(api, page) {
          return api.getJobs(page);
        }]
      },
      onEnter: scrollTop,
      templateUrl: 'partials/jobs.html',
      controller: 'ListJobsCtrl'
    })
    .state('jobdetails', {
      url: '/jobdetails/:jobId',
      parent: 'auth',
      templateUrl: 'partials/jobdetails.html',
      controller: 'JobDetailsController'
    })
    .state('remotecis', {
      url: '/remotecis?page',
      parent: 'auth',
      templateUrl: 'partials/remotecis.html',
      resolve: {
        page: ['$stateParams', function ($stateParams) {
          return parseInt($stateParams.page) || 1;
        }],
        cis: ['api', 'page', function(api, page) {
          return api.getCIs(page);
        }]
      },
      onEnter: scrollTop,
      controller: 'ListCIsCtrl'
    })
    .state('products', {
      url: '/products',
      parent: 'auth',
      templateUrl: 'partials/products.html',
      controller: 'ProductsController'
    })
    .state('stats', {
      url: '/stats',
      parent: 'auth',
      templateUrl: 'partials/stats.html',
      controller: 'StatsController'
    })
    .state('login', {
      url: '/login?next',
      templateUrl: 'partials/login.html',
    });

    $urlRouterProvider.otherwise('/');
  }
])

.controller('authCtrl', [
  '$scope', '$state', 'auth', function ($scope, $state, auth) {
    $scope.isAuthenticated = auth.isAuthenticated;
    $scope.logout = function () {
      auth.logout();
      $state.go('login');
    }
  }
])

.run([
  '$rootScope', '$state', 'authStates',
  function($rootScope, $state, authStates) {
    $rootScope.$on('$stateChangeError', function(_, toState, _, _, _, error) {
      if (error === authStates.DISCONNECTED) {
        $state.go('login', {next: toState.name});
      }
    });
  }
]);

