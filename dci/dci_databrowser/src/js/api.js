require('./app.js')

.factory('api', ['$resource', '$q', function($resource, $q) {
  var Jobs = $resource('/api/jobs/:id');
  var JobStates = $resource('/api/jobstates');
  var JobDefinitions = $resource('/api/jobdefinitions/:id');
  var CIs = $resource('/api/remotecis');

  function getCIs(page) {
    return CIs.get({
      page: page,
      sort: '-created_at'
    }).$promise;
  }

  function getJobs(page) {
    return Jobs.get({
      page: page,
      sort: '-created_at',
      embedded: {
        'jobstates': 1,
        'jobdefinition': 1,
        'remoteci': 1
      },
      projection: {remoteci: 1}
    }).$promise;
  }

  function getJobDefinitions(page) {
    return JobDefinitions.get({
      page: page,
      sort: '-created_at'
    }).$promise;

  }

  function getJobDefinition(id) {
    return JobDefinitions.get({
      'id': id,
      embedded: {'components': 1}
    }).$promise;
  }


  function getJob(id) {
    var job;

    return $q.all([
      Jobs.get({
        'id': id, 'embedded': {'remoteci': 1, 'jobdefinition': 1}
      }).$promise,
      JobStates.get({
        'where': {'job_id': id},
        'sort': 'created_at',
        'embedded': {'files': 1}
      }).$promise
    ]).then(function(data) {
      job = data.shift();
      job.jobstate = data.shift()._items.pop();
      return job;
    });
  }


  return {
    getJobs: getJobs,
    getJob: getJob,
    getJobDefinitions: getJobDefinitions,
    getJobDefinition: getJobDefinition,
    getCIs: getCIs
  }
}]);


