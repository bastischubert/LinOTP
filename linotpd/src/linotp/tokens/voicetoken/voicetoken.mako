# -*- coding: utf-8 -*-
<%doc>
 *
 *   LinOTP - the open source solution for two factor authentication
 *   Copyright (C) 2010 - 2017 KeyIdentity GmbH
 *
 *   This file is part of LinOTP server.
 *
 *   This program is free software: you can redistribute it and/or
 *   modify it under the terms of the GNU Affero General Public
 *   License, version 3, as published by the Free Software Foundation.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU Affero General Public License for more details.
 *
 *   You should have received a copy of the
 *              GNU Affero General Public License
 *   along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 *
 *    E-mail: linotp@keyidentity.com
 *    Contact: www.linotp.org
 *    Support: www.keyidentity.com
 *
 * contains the voice token web interface
</%doc>

%if c.scope == 'enroll.title' :
${_("Voice Token")}
%endif

%if c.scope == 'enroll' :
<script type="text/javascript">

function voice_enroll_setup_defaults(config,options){
    voice_clear_input_fields();
	// in case we enroll voice otp, we get the mobile number of the user
	mobiles = get_selected_mobile();
	$('#voice_phone').val($.trim(mobiles[0]));
    var rand_pin = options['otp_pin_random'];
    if (rand_pin > 0) {
        $("[name='set_pin_rows']").hide();
    } else {
        $("[name='set_pin_rows']").show();
    }
}

/*
 * 'typ'_get_enroll_params()
 *
 * this method is called, when the token  is submitted
 * - it will return a hash of parameters for admin/init call
 *
 */
function voice_get_enroll_params(){
    var params = {};

	params['phone'] 		= 'voice';
    // phone number
    params['phone'] 		= $('#voice_phone').val();
    params['description'] 	=  $('#voice_phone').val() + " " + $('#enroll_voice_desc').val();
    //params['serial'] 		= create_serial('LSSM');

    jQuery.extend(params, add_user_data());

    if ($('#voice_pin1').val() != '') {
        params['pin'] = $('#voice_pin1').val();
    }

    voice_clear_input_fields();
    return params;
}

function voice_clear_input_fields() {
    // Empty input fields for PINs and Keys
    $('#voice_pin1').val('');
    $('#voice_pin2').val('');
}
</script>
<hr>
<p>${_("Please enter the mobile phone number for the Voice token")}</p>
<table>
    <tr>
        <td><label for="voice_phone">${_("Phone number")}</label></td>
        <td><input type="text" name="voice_phone" id="voice_phone" value="" class="text ui-widget-content ui-corner-all"></td>
    </tr>
    <tr>
        <td><label for="enroll_voice_desc" id='enroll_voice_desc_label'>${_("Description")}</label></td>
        <td><input type="text" name="enroll_voice_desc" id="enroll_voice_desc" value="webGUI_generated" class="text"></td>
    </tr>
    <tr name="set_pin_rows" class="space" title='${_("Protect your token with a static PIN")}'><th colspan="2">${_("Token PIN:")}</th></tr>
    <tr name="set_pin_rows">
        <td class="description"><label for="voice_pin1" id="voice_pin1_label">${_("Enter PIN")}:</label></td>
        <td><input type="password" autocomplete="off" name="pin1" id="voice_pin1"
                class="text ui-widget-content ui-corner-all"></td>
    </tr>
    <tr name="set_pin_rows">
        <td class="description"><label for="voice_pin2" id="voice_pin2_label">${_("Confirm PIN")}:</label></td>
        <td><input type="password" autocomplete="off" name="pin2" id="voice_pin2"
                class="text ui-widget-content ui-corner-all"></td>
    </tr>
</table>

% endif



%if c.scope == 'selfservice.title.enroll':
${_("Register VOICE")}
%endif


%if c.scope == 'selfservice.enroll':

<%!
	from linotp.lib.user import getUserPhone
%>
<%
	try:
		phonenumber = getUserPhone(c.authUser, 'mobile')
		if phonenumber == None or len(phonenumber) == 0:
			 phonenumber = ''
	except Exception as e:
		phonenumber = ''
%>

<script type="text/javascript">
	jQuery.extend(jQuery.validator.messages, {
		required:  "${_('required input field')}",
		minlength: "${_('minimum length must be greater than 10')}",
	});

	jQuery.validator.addMethod("phone", function(value, element, param){
        return value.match(/^[+0-9\/\ ]+$/i);
    }, '${_("Please enter a valid phone number. It may only contain numbers and + or /.")}' );

	$('#form_register_voice').validate({
        rules: {
            voice_mobilephone: {
                required: true,
                minlength: 10,
                number: false,
                phone: true
            }
        }
	});

function self_voice_get_param()
{
	var urlparam = {};
	var mobilephone = $('#voice_mobilephone').val();


	urlparam['type'] 		= 'voice';
	urlparam['phone']		= mobilephone;
	urlparam['description'] = mobilephone + '_' + $("#voice_self_desc").val();

	return urlparam;
}

function self_voice_clear()
{
	return true;
}
function self_voice_submit(){

	var ret = false;

	if ($('#form_register_voice').valid()) {
		var params =  self_voice_get_param();
		enroll_token( params );
		//self_voice_clear();
		ret = true;
	} else {
		alert('${_("Form data not valid.")}');
	}
	return ret;
}

</script>

<h1>${_("Register your VOICE OTP Token / mobileTAN")}</h1>
<div id='register_voice_form'>
	<form class="cmxform" id='form_register_voice' action="">
	<fieldset>
		<table>
		<tr>
		<td><label for='voice_mobilephone'>${_("Your mobile phone number")}</label></td>
		<td><input id='voice_mobilephone'
                    name='voice_mobilephone'
                    class="required ui-widget-content ui-corner-all"
                    value='${phonenumber}'

                    %if c.edit_voice == 0:
                           readonly  disabled
                    %endif

                   >
		</td>
		</tr>
		<tr>
		    <td><label for="voice_self_desc" id='voice_self_desc_label'>${_("Description")}</label></td>
		    <td><input type="text" name="voice_self_desc" id="voice_self_desc" value="self_registered"; class="text"></td>
		</tr>
        </table>
        <button class='action-button' id='button_register_voice'
        onclick="self_voice_submit();">${_("register VOICE Token")}</button>
    </fieldset>
    </form>
</div>
% endif


