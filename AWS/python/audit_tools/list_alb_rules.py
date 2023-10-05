import boto3
import json

def get_alb_listener_arns(alb_client, alb_arn):
    listener_arns = []
    response = alb_client.describe_listeners(
        LoadBalancerArn=alb_arn
    )
    listener_arns.extend([listener['ListenerArn'] for listener in response['Listeners']])
    return listener_arns

def get_listener_attributes(alb_client, listener_arn):
    response = alb_client.describe_listeners(
        ListenerArns=[listener_arn]
    )
    listener = response['Listeners'][0]
    port = listener['Port']
    protocol = listener['Protocol']
    return port, protocol

def format_conditions(conditions):
    formatted_conditions = []
    for condition in conditions:
        if condition['Field'] == 'host-header':
            host_values = ', '.join(condition['Values'])
            formatted_conditions.append(f"HTTP Host Header is {host_values}")
        elif condition['Field'] == 'path-pattern':
            path_values = ', '.join(condition['Values'])
            formatted_conditions.append(f"Path Pattern is {path_values}")
        elif condition['Field'] == 'http-header':
            http_header_name = condition['HttpHeaderConfig']['HttpHeaderName']
            http_header_values = ', '.join(condition['HttpHeaderConfig']['Values'])
            formatted_conditions.append(f"HTTP Header {http_header_name} is {http_header_values}")
    return ' AND '.join(formatted_conditions) if formatted_conditions else "If no other rule applies"

def format_actions(actions, alb_client):
    formatted_actions = []
    for action in actions:
        if action['Type'] == 'forward':
            target_group_arn = action['TargetGroupArn']
            target_group_response = alb_client.describe_target_groups(
                TargetGroupArns=[target_group_arn]
            )
            target_group_name = target_group_response['TargetGroups'][0]['TargetGroupName']
            target_group_weight = action['ForwardConfig']['TargetGroups'][0]
            formatted_actions.append(f"Forward to target group:\n{target_group_name} (100%)") # {target_group_arn}:
        elif action['Type'] == 'redirect':
            protocol = action['RedirectConfig']['Protocol']
            port = action['RedirectConfig']['Port']
            host = action['RedirectConfig']['Host']
            path = action['RedirectConfig']['Path']
            query = action['RedirectConfig']['Query']
            status_code = action['RedirectConfig']['StatusCode']
            redirect_info = f"Redirect to {protocol.upper()}://{host}:{port}/{path}?{query}\nStatus code: {status_code}"
            formatted_actions.append(redirect_info)
        elif action['Type'] == 'fixed-response':
            status_code = action['FixedResponseConfig']['StatusCode']
            response_body = action['FixedResponseConfig']['MessageBody']
            content_type = action['FixedResponseConfig']['ContentType']
            fixed_response_info = f"Return fixed response\nResponse code: {status_code}\nResponse body: {response_body}\nResponse content type: {content_type}"
            formatted_actions.append(fixed_response_info)
    return '\n'.join(formatted_actions)
            

def get_alb_rules(alb_client, listener_arn):
    rules = []
    response = alb_client.describe_rules(
        ListenerArn=listener_arn
    )
    rules.extend(response['Rules'])
    while 'NextMarker' in response:
        response = alb_client.describe_rules(
            ListenerArn=listener_arn,
            Marker=response['NextMarker']
        )
        rules.extend(response['Rules'])
    return rules

def main():
    session = boto3.Session(profile_name=f'{cli_profile}')
    alb_client = session.client('elbv2')
    
    alb_paginator = alb_client.get_paginator('describe_load_balancers')
    alb_iterator = alb_paginator.paginate()
    
    for page in alb_iterator:
        for alb in page['LoadBalancers']:
            # Filter for only ALBs
            if alb['Type'] == 'application':
                alb_arn = alb['LoadBalancerArn']
                alb_name = alb['LoadBalancerName']
                listener_arns = get_alb_listener_arns(alb_client, alb_arn)
                
                for listener_arn in listener_arns:
                    # Retrieve listener attributes to get port and protocol
                    port, protocol = get_listener_attributes(alb_client, listener_arn)
                    port_info = f"{protocol}:{port}"
                    
                    # Print ALB and listener information
                    print("=" * 40)
                    print(f"ALB Name: {alb_name}")
                    print(f"Listener ARN: {listener_arn}")
                    print(f"Listener Port: {port_info}")
                    print("=" * 40)
                    
                    
                    rules = get_alb_rules(alb_client, listener_arn)
                    
                    for rule in rules:
                        print(f"Rule ARN: {rule['RuleArn']}")
                        print(f"Priority: {rule['Priority']}")
                        
                        # Format and print conditions
                        formatted_conditions = format_conditions(rule['Conditions'])
                        print(f"Conditions (IF) | {formatted_conditions}")
                        
                        #print(f"Conditions: {rule['Conditions']}") # Print this line if no info is printed, may need additional conditions in format function(s)
                        
                        # Format and print actions
                        formatted_actions = format_actions(rule['Actions'], alb_client)
                        print(f"Actions (THEN) | {formatted_actions}")
                        
                        #print(f"Actions: {rule['Actions']}") # Print this line if no info is printed, may need additional conditions in format function(s)
                        
                        print("=" * 30)
            

if __name__ == "__main__":
    cli_profile = "default"
    main()
