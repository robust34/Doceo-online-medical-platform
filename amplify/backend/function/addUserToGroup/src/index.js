const AWS = require('aws-sdk');
const {StreamChat} = require('stream-chat');
AWS.config.update({
	maxRetries: 2,
	httpOptions: {
		timeout: 6000,
		connectTimeout: 5000,
	},
});

const api_key="a6rmt92za3p7";
const api_secret="jx9tp9jcc3f4b6j8732zynqf7byu4tfbjjah266hskgz7h8vnwngfrpzcg2mddwg";
const stream_roles = {
	"Admins": 'admin',
	"Users": 'user',
	"Doctors": 'doctor'
};

/**
 * @type {import('http').Server}
 */

/**
 * @type {import('@types/aws-lambda').APIGatewayProxyHandler}
 */
exports.handler = async (event, context) => {
	console.log(`EVENT: ${JSON.stringify(event)}`);

	if (event.triggerSource !== 'PostConfirmation_ConfirmSignUp') {
		return event;
	}

	if ( !event.request.userAttributes["custom:groupname"] ) {
		const err = new Error('groupname are required');
		err.statusCode = 400;
		return console.log('Error happened', err);
	}

	try {
		const cognitoIdentityServiceProvider =
      new AWS.CognitoIdentityServiceProvider({apiVersion: '2016-04-18'});
		const params = {
			GroupName: event.request.userAttributes['custom:groupname'], //your confirmed user gets added to this group
			UserPoolId: event.userPoolId,
			Username: event.userName
		};

		await cognitoIdentityServiceProvider
			.adminAddUserToGroup(params)
			.promise();

		const serverClient = new StreamChat(api_key, api_secret);

		await serverClient.upsertUser({
			id: params.Username,
			role: stream_roles[params.GroupName],
			name: event.request.userAttributes['name'] ? event.request.userAttributes['name'] : event.request.userAttributes['preferred_username'],
			birthday: event.request.userAttributes['birthdate'] ? event.request.userAttributes['birthdate'] : ''
		})
    
		return event;
	} catch (err) {
		return console.log('Error happened', err);
	}
};
