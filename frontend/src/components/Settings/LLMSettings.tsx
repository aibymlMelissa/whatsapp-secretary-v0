import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface LLMSettings {
  preferred_provider: string;
  openai_model: string;
  anthropic_model: string;
  gemini_model: string;
  ollama_base_url: string;
  ollama_model: string;
  max_tokens: number;
  temperature: number;
  use_system_default: boolean;
  has_openai_key: boolean;
  has_anthropic_key: boolean;
  has_gemini_key: boolean;
}

interface TestResult {
  success: boolean;
  message: string;
  response_time_ms?: number;
}

export const LLMSettings: React.FC = () => {
  const [settings, setSettings] = useState<LLMSettings>({
    preferred_provider: 'gemini',
    openai_model: 'gpt-4o-mini',
    anthropic_model: 'claude-3-haiku-20240307',
    gemini_model: 'gemini-1.5-flash',
    ollama_base_url: 'http://localhost:11434',
    ollama_model: 'llama3.2',
    max_tokens: 500,
    temperature: 0.7,
    use_system_default: true,
    has_openai_key: false,
    has_anthropic_key: false,
    has_gemini_key: false,
  });

  const [tempApiKeys, setTempApiKeys] = useState({
    openai: '',
    anthropic: '',
    gemini: '',
  });

  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [testResults, setTestResults] = useState<Record<string, TestResult>>({});
  const [isTestingConnection, setIsTestingConnection] = useState<Record<string, boolean>>({});

  const phoneNumber = '+1234567890'; // This should come from user context

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/settings/llm?phone_number=${phoneNumber}`);
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const saveSettings = async () => {
    setIsSaving(true);
    try {
      const payload = {
        ...settings,
        openai_api_key: tempApiKeys.openai || undefined,
        anthropic_api_key: tempApiKeys.anthropic || undefined,
        gemini_api_key: tempApiKeys.gemini || undefined,
      };

      const response = await fetch(`/api/settings/llm?phone_number=${phoneNumber}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const data = await response.json();
        setSettings(data);
        setTempApiKeys({ openai: '', anthropic: '', gemini: '' });
        alert('Settings saved successfully!');
      } else {
        alert('Failed to save settings');
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      alert('Failed to save settings');
    } finally {
      setIsSaving(false);
    }
  };

  const testConnection = async (provider: string) => {
    setIsTestingConnection({ ...isTestingConnection, [provider]: true });

    try {
      const payload: any = { provider };

      if (provider === 'openai' && tempApiKeys.openai) {
        payload.api_key = tempApiKeys.openai;
        payload.model = settings.openai_model;
      } else if (provider === 'anthropic' && tempApiKeys.anthropic) {
        payload.api_key = tempApiKeys.anthropic;
        payload.model = settings.anthropic_model;
      } else if (provider === 'gemini' && tempApiKeys.gemini) {
        payload.api_key = tempApiKeys.gemini;
        payload.model = settings.gemini_model;
      } else if (provider === 'ollama') {
        payload.base_url = settings.ollama_base_url;
        payload.model = settings.ollama_model;
      }

      const response = await fetch('/api/settings/llm/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const result = await response.json();
        setTestResults({ ...testResults, [provider]: result });
      }
    } catch (error) {
      setTestResults({
        ...testResults,
        [provider]: { success: false, message: 'Connection test failed' }
      });
    } finally {
      setIsTestingConnection({ ...isTestingConnection, [provider]: false });
    }
  };

  const removeApiKey = async (provider: string) => {
    try {
      const response = await fetch(`/api/settings/llm/api-key/${provider}?phone_number=${phoneNumber}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setSettings({
          ...settings,
          [`has_${provider}_key`]: false,
        });
        alert(`${provider} API key removed successfully`);
      }
    } catch (error) {
      console.error(`Failed to remove ${provider} API key:`, error);
    }
  };

  const providers = [
    {
      id: 'openai',
      name: 'OpenAI',
      description: 'GPT models from OpenAI',
      models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
      requiresApiKey: true,
    },
    {
      id: 'anthropic',
      name: 'Anthropic',
      description: 'Claude models from Anthropic',
      models: ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'],
      requiresApiKey: true,
    },
    {
      id: 'gemini',
      name: 'Google Gemini',
      description: 'Gemini models from Google',
      models: ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro'],
      requiresApiKey: true,
    },
    {
      id: 'ollama',
      name: 'Ollama',
      description: 'Local open-source models',
      models: ['llama3.2', 'llama3.1', 'codellama', 'mistral'],
      requiresApiKey: false,
    },
  ];

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center">Loading settings...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>LLM Configuration</CardTitle>
        <p className="text-sm text-muted-foreground">
          Configure your AI models and API keys for personalized responses
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Use System Default Toggle */}
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="use-system-default"
            checked={settings.use_system_default}
            onChange={(e) =>
              setSettings({ ...settings, use_system_default: e.target.checked })
            }
            className="rounded border-gray-300"
          />
          <label htmlFor="use-system-default" className="text-sm font-medium">
            Use system default configuration
          </label>
        </div>

        {!settings.use_system_default && (
          <>
            {/* Preferred Provider */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Preferred Provider</label>
              <select
                value={settings.preferred_provider}
                onChange={(e) =>
                  setSettings({ ...settings, preferred_provider: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {providers.map((provider) => (
                  <option key={provider.id} value={provider.id}>
                    {provider.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Provider Configuration Tabs */}
            <Tabs defaultValue="openai" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                {providers.map((provider) => (
                  <TabsTrigger key={provider.id} value={provider.id}>
                    {provider.name}
                  </TabsTrigger>
                ))}
              </TabsList>

              {providers.map((provider) => (
                <TabsContent key={provider.id} value={provider.id} className="space-y-4">
                  <div className="border rounded-lg p-4 space-y-4">
                    <div>
                      <h4 className="font-medium">{provider.name}</h4>
                      <p className="text-sm text-muted-foreground">{provider.description}</p>
                    </div>

                    {provider.requiresApiKey && (
                      <div className="space-y-2">
                        <label className="text-sm font-medium">API Key</label>
                        <div className="flex space-x-2">
                          <input
                            type="password"
                            placeholder={
                              settings[`has_${provider.id}_key` as keyof LLMSettings]
                                ? '••••••••••••••••'
                                : `Enter ${provider.name} API key`
                            }
                            value={tempApiKeys[provider.id as keyof typeof tempApiKeys]}
                            onChange={(e) =>
                              setTempApiKeys({
                                ...tempApiKeys,
                                [provider.id]: e.target.value,
                              })
                            }
                            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                          {settings[`has_${provider.id}_key` as keyof LLMSettings] && (
                            <button
                              onClick={() => removeApiKey(provider.id)}
                              className="px-3 py-2 text-red-600 border border-red-300 rounded-lg hover:bg-red-50"
                            >
                              Remove
                            </button>
                          )}
                        </div>
                      </div>
                    )}

                    {provider.id === 'ollama' && (
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Base URL</label>
                        <input
                          type="url"
                          value={settings.ollama_base_url}
                          onChange={(e) =>
                            setSettings({ ...settings, ollama_base_url: e.target.value })
                          }
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    )}

                    <div className="space-y-2">
                      <label className="text-sm font-medium">Model</label>
                      <select
                        value={settings[`${provider.id}_model` as keyof LLMSettings] as string}
                        onChange={(e) =>
                          setSettings({
                            ...settings,
                            [`${provider.id}_model`]: e.target.value,
                          })
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        {provider.models.map((model) => (
                          <option key={model} value={model}>
                            {model}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Test Connection */}
                    <div className="flex items-center justify-between">
                      <button
                        onClick={() => testConnection(provider.id)}
                        disabled={isTestingConnection[provider.id]}
                        className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
                      >
                        {isTestingConnection[provider.id] ? 'Testing...' : 'Test Connection'}
                      </button>

                      {testResults[provider.id] && (
                        <div
                          className={`text-sm ${
                            testResults[provider.id].success ? 'text-green-600' : 'text-red-600'
                          }`}
                        >
                          {testResults[provider.id].message}
                          {testResults[provider.id].response_time_ms && (
                            <span className="text-gray-500 ml-2">
                              ({testResults[provider.id].response_time_ms}ms)
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </TabsContent>
              ))}
            </Tabs>

            {/* Advanced Settings */}
            <div className="space-y-4 border-t pt-4">
              <h4 className="font-medium">Advanced Settings</h4>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Max Tokens</label>
                  <input
                    type="number"
                    min="1"
                    max="4000"
                    value={settings.max_tokens}
                    onChange={(e) =>
                      setSettings({ ...settings, max_tokens: parseInt(e.target.value) })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Temperature</label>
                  <input
                    type="number"
                    min="0"
                    max="2"
                    step="0.1"
                    value={settings.temperature}
                    onChange={(e) =>
                      setSettings({ ...settings, temperature: parseFloat(e.target.value) })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="text-sm text-muted-foreground">
                <p>
                  <strong>Max Tokens:</strong> Maximum number of tokens in the response (1-4000)
                </p>
                <p>
                  <strong>Temperature:</strong> Controls randomness. Lower = more focused, Higher = more creative (0-2)
                </p>
              </div>
            </div>
          </>
        )}

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            onClick={saveSettings}
            disabled={isSaving}
            className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50"
          >
            {isSaving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </CardContent>
    </Card>
  );
};