import React, { useState, useEffect } from 'react';
import { Phone, Loader, CheckCircle, X } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { API_BASE_URL } from '../../config/api';

interface PhoneConfig {
  phone_number: string;
  toll_free: boolean;
  area_code?: string;
  nickname?: string;
}

const AREA_CODES = [
  '201', '202', '203', '205', '206', '207', '208', '209', '210',
  '212', '213', '214', '215', '216', '217', '218', '219', '224',
  '225', '228', '229', '231', '234', '239', '240', '248', '251',
  '252', '253', '254', '256', '260', '262', '267', '269', '270',
  '272', '276', '281', '301', '302', '303', '304', '305', '307',
  '308', '309', '310', '312', '313', '314', '315', '316', '317',
  '318', '319', '320', '321', '323', '325', '330', '331', '334',
  '336', '337', '339', '346', '347', '351', '352', '360', '361',
  '385', '386', '401', '402', '404', '405', '406', '407', '408',
  '409', '410', '412', '413', '414', '415', '417', '419', '423',
  '424', '425', '430', '432', '434', '435', '440', '442', '443',
  '458', '463', '469', '470', '475', '478', '479', '480', '484',
  '501', '502', '503', '504', '505', '507', '508', '509', '510',
  '512', '513', '515', '516', '517', '518', '520', '530', '534',
  '539', '540', '541', '551', '559', '561', '562', '563', '567',
  '570', '571', '573', '574', '575', '580', '585', '586', '601',
  '602', '603', '605', '606', '607', '608', '609', '610', '612',
  '614', '615', '616', '617', '618', '619', '620', '623', '626',
  '630', '631', '636', '641', '646', '650', '651', '657', '660',
  '661', '662', '667', '669', '678', '681', '682', '701', '702',
  '703', '704', '706', '707', '708', '712', '713', '714', '715',
  '716', '717', '718', '719', '720', '724', '725', '727', '731',
  '732', '734', '737', '740', '747', '754', '757', '760', '762',
  '763', '765', '769', '770', '772', '773', '774', '775', '779',
  '781', '785', '786', '801', '802', '803', '804', '805', '806',
  '808', '810', '812', '813', '814', '815', '816', '817', '818',
  '828', '830', '831', '832', '843', '845', '847', '848', '850',
  '856', '857', '858', '859', '860', '862', '863', '864', '865',
  '870', '872', '878', '901', '903', '904', '906', '907', '908',
  '909', '910', '912', '913', '914', '915', '916', '917', '918',
  '919', '920', '925', '928', '929', '930', '931', '936', '937',
  '940', '941', '947', '949', '951', '952', '954', '956', '959',
  '970', '971', '972', '973', '978', '979', '980', '984', '985',
  '989'
];

const PhoneConfigSection: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [phoneConfig, setPhoneConfig] = useState<PhoneConfig | null>(null);
  const [agentId, setAgentId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Configuration modal state
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [isTollFree, setIsTollFree] = useState(false);
  const [selectedAreaCode, setSelectedAreaCode] = useState('');
  const [nickname, setNickname] = useState('');
  const [isConfiguring, setIsConfiguring] = useState(false);

  useEffect(() => {
    if (user?.practice_id) {
      loadPhoneConfig();
    }
  }, [user?.practice_id]);

  const loadPhoneConfig = async () => {
    if (!user?.practice_id) return;

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      const baseURL = API_BASE_URL;

      // First get the agent to get the agent_id
      const agentResponse = await fetch(`${baseURL}/api/v1/practices/${user.practice_id}/voice-agent`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (agentResponse.status === 404) {
        // No agent exists
        setPhoneConfig(null);
        setAgentId(null);
      } else if (agentResponse.ok) {
        const agentData = await agentResponse.json();
        setAgentId(agentData.agent_id);
        
        if (agentData.phone_number) {
          setPhoneConfig({
            phone_number: agentData.phone_number,
            toll_free: agentData.phone_number.startsWith('1-8') || agentData.phone_number.startsWith('+1-8'),
            area_code: agentData.area_code,
            nickname: agentData.nickname
          });
        } else {
          setPhoneConfig(null);
        }
      } else {
        throw new Error('Failed to load voice agent');
      }
    } catch (err: any) {
      console.error('Error loading phone config:', err);
      setError(err.message || 'Failed to load phone configuration');
    } finally {
      setLoading(false);
    }
  };

  const configurePhoneNumber = async () => {
    if (!user?.practice_id || !agentId) return;
    if (!isTollFree && !selectedAreaCode) return;

    setIsConfiguring(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      const baseURL = API_BASE_URL;
      
      const requestBody: any = {
        toll_free: isTollFree
      };

      if (!isTollFree && selectedAreaCode) {
        requestBody.area_code = parseInt(selectedAreaCode);
      }

      if (nickname.trim()) {
        requestBody.nickname = nickname.trim();
      }

      console.log('📞 Configuring phone number:', requestBody);

      const response = await fetch(`${baseURL}/api/v1/practices/${user.practice_id}/voice-agent/${agentId}/register-phone`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to configure phone number');
      }

      const data = await response.json();
      console.log('✅ Phone number configured:', data);

      // Reload the config
      await loadPhoneConfig();
      
      // Close modal and reset form
      setShowConfigModal(false);
      setIsTollFree(false);
      setSelectedAreaCode('');
      setNickname('');
    } catch (err: any) {
      console.error('❌ Error configuring phone:', err);
      setError(err.message || 'Failed to configure phone number');
    } finally {
      setIsConfiguring(false);
    }
  };

  const formatPhoneNumber = (phone: string) => {
    // Format phone number for display
    return phone || 'Not configured';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  if (error && !phoneConfig) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-800">{error}</p>
      </div>
    );
  }

  // Empty state - no agent exists
  if (!agentId) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
        <Phone className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Voice Agent</h3>
        <p className="text-sm text-gray-500 mb-6">
          You need to create a voice agent first before configuring a phone number.
        </p>
        <p className="text-xs text-gray-400">
          Go to the Agents tab to create your voice agent.
        </p>
      </div>
    );
  }

  // No phone configured yet
  if (!phoneConfig) {
    return (
      <>
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <Phone className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Configure Phone Number</h3>
          <p className="text-sm text-gray-500 mb-6">
            Set up a phone number for your voice agent to handle incoming calls.
          </p>
          <button
            onClick={() => setShowConfigModal(true)}
            className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            <Phone className="w-4 h-4 mr-2" />
            Configure Phone Number
          </button>
        </div>

        {/* Configuration Modal */}
        {showConfigModal && (
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900">Configure Phone Number</h3>
                <button
                  onClick={() => {
                    setShowConfigModal(false);
                    setError(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {error && (
                <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-3">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}

              <div className="space-y-4">
                {/* Toll-Free Toggle */}
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700">
                    Toll-Free Number
                  </label>
                  <button
                    onClick={() => {
                      setIsTollFree(!isTollFree);
                      if (!isTollFree) {
                        setSelectedAreaCode('');
                      }
                    }}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      isTollFree ? 'bg-blue-600' : 'bg-gray-200'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        isTollFree ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                {/* Area Code Picker */}
                {!isTollFree && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Area Code
                    </label>
                    <select
                      value={selectedAreaCode}
                      onChange={(e) => setSelectedAreaCode(e.target.value)}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">Select Area Code</option>
                      {AREA_CODES.map(code => (
                        <option key={code} value={code}>{code}</option>
                      ))}
                    </select>
                  </div>
                )}

                {/* Nickname */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nickname (optional)
                  </label>
                  <input
                    type="text"
                    value={nickname}
                    onChange={(e) => setNickname(e.target.value)}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g., Main Reception Line"
                  />
                </div>

                {/* Pricing Info */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Pricing Information</h4>
                  <div className="space-y-1 text-sm">
                    {isTollFree ? (
                      <p className="text-gray-700">Toll-Free: <span className="font-semibold">$1/month</span></p>
                    ) : (
                      <p className="text-gray-700">Regular Line: <span className="font-semibold">$10/month</span></p>
                    )}
                    <p className="text-xs text-gray-600">Plus 20¢/minute for calls</p>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => {
                    setShowConfigModal(false);
                    setError(null);
                  }}
                  disabled={isConfiguring}
                  className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={configurePhoneNumber}
                  disabled={isConfiguring || (!isTollFree && !selectedAreaCode)}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isConfiguring ? (
                    <>
                      <Loader className="w-4 h-4 mr-2 animate-spin" />
                      Configuring...
                    </>
                  ) : (
                    'Configure'
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </>
    );
  }

  // Phone is configured - show details
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="border-b border-gray-200 px-6 py-4">
          <div className="flex items-center space-x-2">
            <Phone className="w-5 h-5 text-gray-600" />
            <h3 className="text-lg font-semibold text-gray-900">Phone Configuration</h3>
            <CheckCircle className="w-5 h-5 text-green-500 ml-2" />
          </div>
        </div>

        <div className="overflow-hidden">
          <table className="min-w-full">
            <tbody className="divide-y divide-gray-200">
              <tr>
                <td className="px-4 py-3 text-sm font-medium text-gray-500 bg-gray-50 w-1/3">
                  <span>Phone Number</span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-900">
                  {formatPhoneNumber(phoneConfig.phone_number)}
                </td>
              </tr>
              <tr>
                <td className="px-4 py-3 text-sm font-medium text-gray-500 bg-gray-50">
                  <span>Type</span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-900">
                  {phoneConfig.toll_free ? 'Toll-Free' : 'Regular Line'}
                </td>
              </tr>
              {phoneConfig.area_code && (
                <tr>
                  <td className="px-4 py-3 text-sm font-medium text-gray-500 bg-gray-50">
                    <span>Area Code</span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {phoneConfig.area_code}
                  </td>
                </tr>
              )}
              {phoneConfig.nickname && (
                <tr>
                  <td className="px-4 py-3 text-sm font-medium text-gray-500 bg-gray-50">
                    <span>Nickname</span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {phoneConfig.nickname}
                  </td>
                </tr>
              )}
              <tr>
                <td className="px-4 py-3 text-sm font-medium text-gray-500 bg-gray-50">
                  <span>Monthly Cost</span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-900">
                  {phoneConfig.toll_free ? '$15/month' : '$10/month'} <span className="text-gray-500">+ 20¢/min</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default PhoneConfigSection;

