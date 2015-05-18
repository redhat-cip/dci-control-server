// Define the application
var app = angular.module('app', ['restangular']);

// Configure the application
app.config(function(RestangularProvider) {
    RestangularProvider.setBaseUrl(
        'http://127.0.0.1:5000/api');
    RestangularProvider.setDefaultRequestParams('get');
    // Note that we run everything on the localhost
});

// Define the controller
app.controller('mainCtrl', function($scope, $q, $location, Restangular) {
    function aggregate_job_info(job) {
	this.push(Restangular.one('testversions', job.testversion_id).get().then(
	    function(test_version) {
		var remoteci = Restangular.one('remotecis', job.remoteci_id).get();
		var test = Restangular.one('tests', test_version.test_id).get();
		var version = Restangular.one('versions', test_version.version_id).get();
		// TODO(Gonéri): We can improve performance here.
		var jobstates = Restangular.all('jobstates', {"where": { "job_id": job.id}, "sort": [("created_at", "-1", "nullslast")]}).getList().then(function(data) {return data._items;});
		job.remoteci = remoteci;
		job.test = test;
		job.version = version;
		job.jobstates = jobstates;
		return job;
	    }
	));
    }
    var searchObject = $location.search();
    var base_jobs = Restangular.all('jobs');

    base_jobs.getList({"page": searchObject.page}).then(
	function(jobs) {
	var promises = [];
	angular.forEach(jobs._items, aggregate_job_info, promises);

	$scope._meta = jobs._meta;
	$scope._link = jobs._link;
	$scope.jobs = promises;

	});
});
