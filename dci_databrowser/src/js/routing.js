
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
    .state('job', {
      url: '/jobs/:id',
      parent: 'auth',
      templateUrl: 'partials/job.html',
      resolve: {
        job: ['$stateParams', 'api', function($stateParams, api) {
          return api.getJob($stateParams.id);
        }]
      },
      controller: 'JobCtrl'
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
      resolve: {
        products: ['api', function(api) {
          return api.getProducts
        }]
      },
      templateUrl: 'partials/products.html',
      controller: 'ProductsCtrl'
    })
    .state('stats', {
      url: '/stats',
      parent: 'auth',
      templateUrl: 'partials/stats.html',
      controller: 'StatsController'
    })
    .state('login', {
      url: '/login?next&args',
      controller: 'LoginCtrl',
      resolve: {
        next: ['$stateParams', function($stateParams) {
          return {
            state: $stateParams.next || 'index',
            args: $stateParams.args &&
              angular.fromJson(atob($stateParams.args)) || {}
          };
        }]
      },
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
    $rootScope.$on(
      '$stateChangeError', function(_, toState, toParams, _, _, error) {
        if (error === authStates.DISCONNECTED) {
          $state.go('login', {
            next: toState.name,
            args: btoa(angular.toJson(toParams))
          });
        }
      }
    );
  }
]);

