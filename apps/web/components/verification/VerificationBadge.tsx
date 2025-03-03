import React, { useState, useEffect } from 'react';
import { Box, Badge, Tooltip, Text, Flex, Spinner, Button, Modal, ModalOverlay, ModalContent, ModalHeader, ModalBody, ModalCloseButton, useDisclosure, Image, Link, VStack, HStack, Divider } from '@chakra-ui/react';
import { CheckCircleIcon, WarningIcon, InfoIcon, ExternalLinkIcon, LockIcon } from '@chakra-ui/icons';

interface VerificationData {
  verified: boolean;
  issuer: string;
  timestamp: string;
  verification_url: string;
  qr_code?: string;
  transaction_id?: string;
  block_number?: number;
  network?: string;
  contract_address?: string;
}

interface VerificationBadgeProps {
  canvasId: string;
  size?: 'sm' | 'md' | 'lg';
  showDetails?: boolean;
  onVerify?: () => void;
}

const VerificationBadge: React.FC<VerificationBadgeProps> = ({
  canvasId,
  size = 'md',
  showDetails = false,
  onVerify
}) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [verificationData, setVerificationData] = useState<VerificationData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchVerificationData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch verification data from API
        const response = await fetch(`/api/v1/blockchain/canvas/${canvasId}/badge`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch verification data: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.success && data.data) {
          setVerificationData(data.data);
        } else {
          setError(data.message || 'Failed to fetch verification data');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
      } finally {
        setLoading(false);
      }
    };
    
    if (canvasId) {
      fetchVerificationData();
    }
  }, [canvasId]);

  const getBadgeColor = () => {
    if (!verificationData) return 'gray';
    return verificationData.verified ? 'green' : 'red';
  };

  const getBadgeText = () => {
    if (loading) return 'Checking...';
    if (error) return 'Verification Error';
    if (!verificationData) return 'Not Verified';
    return verificationData.verified ? 'Verified' : 'Not Verified';
  };

  const getBadgeIcon = () => {
    if (loading) return <Spinner size="xs" />;
    if (error) return <WarningIcon />;
    if (!verificationData) return <InfoIcon />;
    return verificationData.verified ? <CheckCircleIcon /> : <WarningIcon />;
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString();
    } catch (err) {
      return dateString;
    }
  };

  const handleVerifyClick = () => {
    if (onVerify) {
      onVerify();
    }
  };

  const renderBadge = () => (
    <Badge
      colorScheme={getBadgeColor()}
      variant="solid"
      borderRadius="full"
      px={size === 'sm' ? 2 : size === 'md' ? 3 : 4}
      py={size === 'sm' ? 1 : size === 'md' ? 1 : 2}
      fontSize={size === 'sm' ? 'xs' : size === 'md' ? 'sm' : 'md'}
      cursor="pointer"
      onClick={onOpen}
      display="flex"
      alignItems="center"
    >
      <Box mr={1}>{getBadgeIcon()}</Box>
      {getBadgeText()}
    </Badge>
  );

  const renderDetailsModal = () => (
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>
          <Flex alignItems="center">
            <LockIcon mr={2} />
            Trust Verification Details
          </Flex>
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody pb={6}>
          {loading ? (
            <Flex justifyContent="center" alignItems="center" minHeight="200px">
              <Spinner size="xl" />
            </Flex>
          ) : error ? (
            <Box textAlign="center" p={4}>
              <WarningIcon color="red.500" boxSize={10} mb={4} />
              <Text color="red.500">{error}</Text>
              <Button mt={4} onClick={handleVerifyClick} colorScheme="blue">
                Verify Now
              </Button>
            </Box>
          ) : !verificationData ? (
            <Box textAlign="center" p={4}>
              <InfoIcon color="blue.500" boxSize={10} mb={4} />
              <Text>This content has not been verified yet.</Text>
              <Button mt={4} onClick={handleVerifyClick} colorScheme="blue">
                Verify Now
              </Button>
            </Box>
          ) : (
            <VStack spacing={6} align="stretch">
              <Flex 
                justifyContent="center" 
                alignItems="center" 
                bg={verificationData.verified ? "green.50" : "red.50"} 
                p={4} 
                borderRadius="md"
              >
                {verificationData.verified ? (
                  <CheckCircleIcon color="green.500" boxSize={8} mr={3} />
                ) : (
                  <WarningIcon color="red.500" boxSize={8} mr={3} />
                )}
                <Text fontSize="lg" fontWeight="bold">
                  {verificationData.verified 
                    ? "Content Verified" 
                    : "Content Not Verified"}
                </Text>
              </Flex>
              
              <Box>
                <Text fontWeight="bold" mb={1}>Issuer</Text>
                <Text>{verificationData.issuer}</Text>
              </Box>
              
              <Box>
                <Text fontWeight="bold" mb={1}>Verification Date</Text>
                <Text>{formatDate(verificationData.timestamp)}</Text>
              </Box>
              
              {verificationData.transaction_id && (
                <Box>
                  <Text fontWeight="bold" mb={1}>Transaction ID</Text>
                  <Text fontSize="sm" fontFamily="monospace" overflowWrap="break-word">
                    {verificationData.transaction_id}
                  </Text>
                </Box>
              )}
              
              {verificationData.block_number && (
                <Box>
                  <Text fontWeight="bold" mb={1}>Block Number</Text>
                  <Text>{verificationData.block_number}</Text>
                </Box>
              )}
              
              {verificationData.network && (
                <Box>
                  <Text fontWeight="bold" mb={1}>Blockchain Network</Text>
                  <Text>{verificationData.network}</Text>
                </Box>
              )}
              
              <Divider />
              
              <HStack spacing={8} justify="space-between">
                {verificationData.qr_code && (
                  <Box>
                    <Text fontWeight="bold" mb={2} textAlign="center">Verification QR Code</Text>
                    <Box p={2} bg="white" borderRadius="md" boxShadow="sm">
                      <Image src={verificationData.qr_code} alt="Verification QR Code" boxSize="150px" />
                    </Box>
                  </Box>
                )}
                
                <VStack align="start" flex={1}>
                  <Text fontWeight="bold">Verify Online</Text>
                  <Text fontSize="sm">
                    You can verify this content online by visiting the verification page.
                  </Text>
                  <Link 
                    href={verificationData.verification_url} 
                    isExternal 
                    color="blue.500"
                    mt={2}
                  >
                    <Button rightIcon={<ExternalLinkIcon />} colorScheme="blue" size="sm">
                      Verify Online
                    </Button>
                  </Link>
                </VStack>
              </HStack>
              
              {verificationData.contract_address && (
                <Box mt={4} fontSize="xs" color="gray.500">
                  <Text>Contract Address: {verificationData.contract_address}</Text>
                </Box>
              )}
            </VStack>
          )}
        </ModalBody>
      </ModalContent>
    </Modal>
  );

  return (
    <>
      {showDetails ? (
        <Box p={4} borderWidth={1} borderRadius="md" borderColor={getBadgeColor()}>
          <Flex justifyContent="space-between" alignItems="center" mb={2}>
            {renderBadge()}
            {!loading && !error && verificationData && (
              <Text fontSize="sm" color="gray.500">
                {formatDate(verificationData.timestamp)}
              </Text>
            )}
          </Flex>
          {!loading && !error && verificationData && (
            <Text fontSize="sm">
              Issued by: {verificationData.issuer}
            </Text>
          )}
        </Box>
      ) : (
        <Tooltip 
          label={loading ? "Checking verification status..." : error ? error : verificationData?.verified ? "Content verified" : "Content not verified"}
          placement="top"
          hasArrow
        >
          {renderBadge()}
        </Tooltip>
      )}
      {renderDetailsModal()}
    </>
  );
};

export default VerificationBadge;
